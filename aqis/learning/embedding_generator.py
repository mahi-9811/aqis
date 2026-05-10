from __future__ import annotations

import hashlib
from typing import Any


class EmbeddingGenerator:
    """Generate local embeddings, falling back to deterministic hashed vectors."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._model = None
        self._model_unavailable = False

    def generate_embedding(self, text: str) -> list[float]:
        cleaned = str(text or "").strip()
        if not cleaned:
            return [0.0] * 32
        try:
            model = self._load_model()
            if model is not None:
                vector = model.encode(cleaned, normalize_embeddings=True)
                return [float(value) for value in vector.tolist()]
        except Exception:
            self._model = None
            self._model_unavailable = True
        return self._hashed_embedding(cleaned)

    def _load_model(self) -> Any:
        if self._model_unavailable:
            return None
        if self._model is not None:
            return self._model
        try:
            from sentence_transformers import SentenceTransformer
        except Exception:
            return None
        try:
            self._model = SentenceTransformer(self.model_name, local_files_only=True)
        except Exception:
            self._model_unavailable = True
            return None
        return self._model

    def _hashed_embedding(self, text: str) -> list[float]:
        # Deterministic fallback for environments without sentence-transformers.
        values = [0.0] * 32
        for index, token in enumerate(text.lower().split()):
            digest = hashlib.sha256(f"{index}:{token}".encode("utf-8")).digest()
            for offset in range(32):
                values[offset] += digest[offset] / 255.0
        magnitude = sum(value * value for value in values) ** 0.5 or 1.0
        return [round(value / magnitude, 6) for value in values]

    # TODO: replace the fallback path with a bundled local model package once
    # the deployment environment guarantees sentence-transformers availability.
