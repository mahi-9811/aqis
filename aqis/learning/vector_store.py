from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from aqis.core.config import get_config


VECTOR_STORE_PATH = get_config().vector_store_path


class VectorStore:
    """Persist vectors and provide similarity search with FAISS or fallback cosine scan."""

    def __init__(self, path: Path = VECTOR_STORE_PATH) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._records: list[dict[str, Any]] | None = None

    def add_vector(self, id: str, vector: list[float], metadata: dict[str, Any]) -> None:
        records = self._load_records()
        records = [record for record in records if record["id"] != id]
        records.append({"id": id, "vector": vector, "metadata": metadata})
        self._records = records
        self._save_records(records)

    def search_similar(self, vector: list[float], top_k: int = 5) -> list[dict[str, Any]]:
        records = self._load_records()
        if not records:
            return []
        try:
            return self._search_faiss(vector, records, top_k)
        except Exception:
            return self._search_fallback(vector, records, top_k)

    def stats(self) -> dict[str, Any]:
        records = self._load_records()
        return {
            "vectorCount": len(records),
            "backend": "faiss" if self._faiss_available() else "fallback",
        }

    def _load_records(self) -> list[dict[str, Any]]:
        if self._records is not None:
            return list(self._records)
        if not self.path.exists():
            self._records = []
            return []
        with self.path.open("r", encoding="utf-8") as handle:
            self._records = json.load(handle)
        return list(self._records)

    def _save_records(self, records: list[dict[str, Any]]) -> None:
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(records, handle, ensure_ascii=False, indent=2)

    def _search_faiss(self, vector: list[float], records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        import faiss
        import numpy as np

        matrix = np.array([record["vector"] for record in records], dtype="float32")
        query = np.array([vector], dtype="float32")
        index = faiss.IndexFlatIP(matrix.shape[1])
        index.add(matrix)
        scores, positions = index.search(query, min(top_k, len(records)))

        results: list[dict[str, Any]] = []
        for score, position in zip(scores[0], positions[0]):
            if position < 0:
                continue
            record = records[int(position)]
            results.append(
                {
                    "id": record["id"],
                    "score": float(score),
                    "metadata": record["metadata"],
                }
            )
        return results

    def _search_fallback(self, vector: list[float], records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        scored: list[dict[str, Any]] = []
        for record in records:
            score = _cosine_similarity(vector, record["vector"])
            scored.append({"id": record["id"], "score": score, "metadata": record["metadata"]})
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]

    def _faiss_available(self) -> bool:
        try:
            import faiss  # noqa: F401
        except Exception:
            return False
        return True


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = sum(value * value for value in left) ** 0.5 or 1.0
    right_norm = sum(value * value for value in right) ** 0.5 or 1.0
    return round(dot / (left_norm * right_norm), 6)
