from __future__ import annotations

from typing import Any

from aqis.agents.base_agent import BaseAgent
from aqis.risk_engine.feature_extractor import extract_features
from aqis.risk_engine.history_manager import RunHistoryManager


class ContextRetrieverAgent(BaseAgent):
    """Pull relevant historical patterns for the same test case."""

    agent_name = "context_retriever"

    def __init__(self, history_manager: RunHistoryManager | None = None) -> None:
        super().__init__()
        self.history_manager = history_manager or RunHistoryManager()

    def run(self, bundle: dict[str, Any], previous_output: dict[str, Any] | None = None) -> dict[str, Any]:
        self.validate_bundle(bundle)
        self.log_start(bundle)

        failure_categories = []
        if previous_output:
            failure_categories = list(previous_output.get("failureCategories") or [])

        runs = self.history_manager.load_runs(bundle["testName"])
        current_features = extract_features(bundle)
        insights: list[str] = []

        for run in runs[-5:]:
            run_features = extract_features(run)
            if failure_categories and self._matches_category(failure_categories, run_features):
                insights.append(
                    f"Historical run showed similar {failure_categories[0].lower().replace('_', ' ')} pattern"
                )
            if int(run_features.get("autoheal_failures", 0)) > 0:
                insights.append("AutoHeal failed in a previous run")
            if int(run_features.get("environmentErrorCount", 0)) > 0:
                insights.append("Environment errors appeared in earlier runs")
            if run_features.get("missingElements", 0) and current_features.get("missingElements", 0):
                insights.append("Missing element pattern repeated across runs")

        ordered_insights = self.unique_ordered(insights)
        result = {
            "similarFailuresFound": bool(ordered_insights),
            "historicalInsights": ordered_insights,
            "historyCount": len(runs),
        }
        # TODO: augment retrieval with vector search over historical RCA summaries.
        self.log_end(result)
        return result

    def _matches_category(self, categories: list[str], features: dict[str, Any]) -> bool:
        if "PAGE_LOAD_TIMING" in categories and bool(features.get("screenNotReady", 0)):
            return True
        if "LOCATOR_NOT_FOUND" in categories and int(features.get("missingElements", 0)) > 0:
            return True
        if "FLAKY_TEST" in categories and int(features.get("retries", 0)) > 1:
            return True
        if "ENVIRONMENT_INSTABILITY" in categories and int(features.get("environmentErrorCount", 0)) > 0:
            return True
        return False
