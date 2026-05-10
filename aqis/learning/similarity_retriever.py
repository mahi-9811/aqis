from __future__ import annotations

from typing import Any

from aqis.learning.embedding_generator import EmbeddingGenerator
from aqis.learning.knowledge_store import KnowledgeStore
from aqis.learning.vector_store import VectorStore


class SimilarityRetriever:
    """Retrieve similar historical cases using stored embeddings and metadata."""

    def __init__(
        self,
        knowledge_store: KnowledgeStore | None = None,
        embedding_generator: EmbeddingGenerator | None = None,
        vector_store: VectorStore | None = None,
    ) -> None:
        self.knowledge_store = knowledge_store or KnowledgeStore()
        self.embedding_generator = embedding_generator or EmbeddingGenerator()
        self.vector_store = vector_store or VectorStore()

    def retrieve(self, bundle: dict[str, Any], top_k: int = 5) -> dict[str, Any]:
        summary_text = self._build_summary_text(bundle)
        vector = self.embedding_generator.generate_embedding(summary_text)
        results = self.vector_store.search_similar(vector, top_k=top_k)

        matches: list[dict[str, Any]] = []
        for result in results:
            metadata = result["metadata"]
            matches.append(
                {
                    "testName": metadata.get("testName"),
                    "failureCategory": metadata.get("failureCategory"),
                    "fixApplied": metadata.get("fixType"),
                    "confidence": round(float(result["score"]), 2),
                    "timestamp": metadata.get("timestamp"),
                }
            )

        return {
            "similarCasesFound": bool(matches),
            "matches": matches,
        }

    def retrieve_for_test(self, test_name: str, top_k: int = 5) -> dict[str, Any]:
        records = self.knowledge_store.load_knowledge(test_name)
        matches = [
            {
                "testName": record.get("testName"),
                "failureCategory": record.get("failureCategory"),
                "fixApplied": record.get("fixSummary", {}).get("recommendedFixType"),
                "confidence": round(float(record.get("confidenceScore", 0.0)), 2),
                "timestamp": record.get("timestamp"),
            }
            for record in records[-top_k:]
        ]
        return {
            "similarCasesFound": bool(matches),
            "matches": list(reversed(matches)),
        }

    def _build_summary_text(self, bundle: dict[str, Any]) -> str:
        step_text = " ".join(str(step.get("stepName") or "") for step in bundle.get("steps") or [])
        exception_text = " ".join(str(item) for item in bundle.get("exception") or [])
        return " | ".join(
            [
                str(bundle.get("testName") or ""),
                step_text,
                exception_text,
                str(bundle.get("ocrText") or "")[:250],
            ]
        )
