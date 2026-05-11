from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from aqis.learning.embedding_generator import EmbeddingGenerator
from aqis.learning.knowledge_store import KnowledgeStore
from aqis.learning.similarity_retriever import SimilarityRetriever
from aqis.learning.vector_store import VectorStore

knowledge_store = KnowledgeStore()
embedding_generator = EmbeddingGenerator()
vector_store = VectorStore()
similarity_retriever = SimilarityRetriever(
    knowledge_store=knowledge_store,
    embedding_generator=embedding_generator,
    vector_store=vector_store,
)


def update_knowledge(
    bundle: dict[str, Any],
    agent_output: dict[str, Any],
    autofix_output: dict[str, Any],
    risk_report: dict[str, Any] | None = None,
    generated_tests: dict[str, Any] | None = None,
    feedback: dict[str, Any] | None = None,
) -> dict[str, Any]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    failure = agent_output.get("agents", {}).get("failureAnalyzer", {})
    validation = agent_output.get("agents", {}).get("validation", {})

    run_summary = {
        "id": f"{bundle.get('testName', 'unknown')}::{timestamp}",
        "timestamp": timestamp,
        "testName": bundle.get("testName"),
        "failureCategory": failure.get("failureCategory"),
        "failureCategories": failure.get("failureCategories", []),
        "rootCauses": failure.get("rootCauses", []),
        "riskScore": risk_report.get("riskScore") if risk_report else None,
        "riskLevel": risk_report.get("riskLevel") if risk_report else None,
        "confidenceScore": validation.get("confidenceScore", autofix_output.get("confidence", 0.0)),
        "fixSummary": {
            "recommendedFixType": autofix_output.get("fixes", [{}])[0].get("fixType") if autofix_output.get("fixes") else None,
            "recommended": autofix_output.get("recommended", False),
            "message": autofix_output.get("message"),
        },
        "generatedTestCount": len((generated_tests or {}).get("generatedTests", [])),
        "feedback": feedback or {"fixOutcome": "pending"},
    }
    knowledge_store.store_run_knowledge(run_summary)

    summary_text = _knowledge_text(bundle, agent_output, autofix_output)
    vector = embedding_generator.generate_embedding(summary_text)
    vector_store.add_vector(
        id=run_summary["id"],
        vector=vector,
        metadata={
            "testName": run_summary["testName"],
            "failureCategory": run_summary["failureCategory"],
            "fixType": run_summary["fixSummary"]["recommendedFixType"],
            "timestamp": run_summary["timestamp"],
        },
    )
    return run_summary


def retrieve_prior_knowledge(bundle: dict[str, Any]) -> dict[str, Any]:
    return similarity_retriever.retrieve(bundle)


def record_feedback(payload: dict[str, Any]) -> dict[str, Any]:
    test_name = str(payload.get("testName") or "").strip()
    if not test_name:
        raise ValueError("testName is required")
    outcome = str(payload.get("fixOutcome", "manual_override") or "manual_override").lower()
    feedback_weight = _feedback_weight(outcome)
    base_confidence = _bounded_float(payload.get("confidenceScore", 0.0))
    adjusted_confidence = round(max(0.0, min(1.0, base_confidence + feedback_weight)), 3)
    entry = {
        "id": f"feedback::{test_name}::{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')}",
        "timestamp": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ"),
        "testName": test_name,
        "failureCategory": payload.get("failureCategory"),
        "feedback": {
            "fixOutcome": outcome,
            "notes": payload.get("notes", ""),
            "weight": feedback_weight,
        },
        "confidenceScore": adjusted_confidence,
        "originalConfidenceScore": base_confidence,
        "fixSummary": {
            "recommendedFixType": payload.get("fixType"),
            "recommended": payload.get("recommended", False),
            "message": "Feedback event",
        },
    }
    knowledge_store.store_run_knowledge(entry)
    return {"stored": True, "entry": entry, "feedbackWeight": feedback_weight}


def learning_stats() -> dict[str, Any]:
    return {
        **knowledge_store.stats(),
        **vector_store.stats(),
    }


def _knowledge_text(bundle: dict[str, Any], agent_output: dict[str, Any], autofix_output: dict[str, Any]) -> str:
    failure = agent_output.get("agents", {}).get("failureAnalyzer", {})
    report = agent_output.get("finalReport", {})
    fix_line = " ".join(fix.get("description", "") for fix in autofix_output.get("fixes", []))
    return " | ".join(
        [
            str(bundle.get("testName") or ""),
            str(failure.get("failureCategory") or ""),
            " ".join(str(cause) for cause in failure.get("rootCauses", [])),
            str(report.get("summary") or ""),
            fix_line,
            str(bundle.get("ocrText") or "")[:250],
        ]
    )


def _bounded_float(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except Exception:
        return 0.0


def _feedback_weight(outcome: str) -> float:
    if outcome in {"success", "fixed", "accepted", "pass"}:
        return 0.15
    if outcome in {"failure", "failed", "rejected", "regression"}:
        return -0.2
    if outcome in {"partial", "manual_override"}:
        return 0.0
    return 0.0
