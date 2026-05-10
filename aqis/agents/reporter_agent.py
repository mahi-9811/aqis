from __future__ import annotations

from typing import Any

from aqis.agents.base_agent import BaseAgent


class ReportAgent(BaseAgent):
    """Compose a structured RCA report from prior agent outputs."""

    agent_name = "reporter"

    def run(self, bundle: dict[str, Any], previous_output: dict[str, Any] | None = None) -> dict[str, Any]:
        self.validate_bundle(bundle)
        self.log_start(bundle)

        state = previous_output or {}
        reader = state.get("test_reader", {})
        failure = state.get("failure_analyzer", {})
        retrieved = state.get("context_retriever", {})
        validation = state.get("validation", {})

        fixes = list(validation.get("approvedFixes") or state.get("fix_suggestion", {}).get("fixes") or [])
        root_causes = list(failure.get("rootCauses") or ["Root cause not identified"])
        risk_level = self._risk_level(failure, validation)

        result = {
            "summary": (
                f"{reader.get('testIntent', bundle.get('testName', 'Unknown test'))} failed during "
                f"{reader.get('stepSummary', 'an unknown step')} due to {failure.get('failureCategory', 'UNKNOWN_FAILURE')}."
            ),
            "rootCause": root_causes[0],
            "recommendedFix": fixes[0] if fixes else "No approved fix recommendation available",
            "riskLevel": risk_level,
            "historicalContext": list(retrieved.get("historicalInsights") or []),
        }
        # TODO: have an LLM generate richer user-facing RCA narratives from the
        # structured evidence once deterministic safeguards are in place.
        self.log_end(result)
        return result

    def _risk_level(self, failure: dict[str, Any], validation: dict[str, Any]) -> str:
        categories = list(failure.get("failureCategories") or [])
        confidence = float(validation.get("confidenceScore", 0.0))
        if "ENVIRONMENT_INSTABILITY" in categories or "FLAKY_TEST" in categories:
            return "HIGH"
        if confidence >= 0.8:
            return "MEDIUM"
        return "LOW"
