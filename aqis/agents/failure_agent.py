from __future__ import annotations

from typing import Any

from aqis.agents.base_agent import BaseAgent
from aqis.risk_engine.feature_extractor import extract_features


class FailureAnalyzerAgent(BaseAgent):
    """Classify likely root causes from deterministic bundle heuristics."""

    agent_name = "failure_analyzer"

    def run(self, bundle: dict[str, Any], previous_output: dict[str, Any] | None = None) -> dict[str, Any]:
        self.validate_bundle(bundle)
        self.log_start(bundle)

        features = extract_features(bundle)
        categories: list[str] = []
        root_causes: list[str] = []

        error_text = " ".join(
            self.safe_text(step.get("errorMessage")) for step in bundle.get("steps") or []
        ).lower()
        exception_text = " ".join(self.safe_text(value) for value in self.listify(bundle.get("exception"))).lower()
        combined_text = f"{error_text} {exception_text}".strip()

        if "no such element" in combined_text or "nosuchelement" in combined_text or "elementnotfound" in combined_text:
            categories.append("LOCATOR_NOT_FOUND")
            root_causes.extend(
                [
                    "Target element was not found in the DOM at execution time",
                    "Locator may be stale, dynamic, or incorrectly scoped",
                ]
            )

        if features.get("screenNotReady", 0):
            categories.append("PAGE_LOAD_TIMING")
            root_causes.extend(
                [
                    "Dynamic header not loaded",
                    "Page scanned too early",
                ]
            )

        if int(features.get("retries", 0)) > 1:
            categories.append("FLAKY_TEST")
            root_causes.extend(
                [
                    "Test required multiple retries before stabilizing",
                    "Intermittent timing or UI synchronization issue detected",
                ]
            )

        if int(features.get("sap_ui5_errors", 0)) > 0 or int(features.get("environmentErrorCount", 0)) >= 2:
            categories.append("ENVIRONMENT_INSTABILITY")
            root_causes.extend(
                [
                    "SAP UI5 or environment-side errors were observed",
                    "Test environment appears unstable or partially unavailable",
                ]
            )

        if not categories:
            categories.append("UNKNOWN_FAILURE")
            root_causes.append("No strong deterministic failure pattern matched the bundle")

        primary_category = categories[0]
        result = {
            "failureCategory": primary_category,
            "failureCategories": self.unique_ordered(categories),
            "rootCauses": self.unique_ordered(root_causes),
            "featuresUsed": {
                "retries": int(features.get("retries", 0)),
                "screenNotReady": bool(features.get("screenNotReady", 0)),
                "sapUi5Errors": int(features.get("sap_ui5_errors", 0)),
                "environmentErrorCount": int(features.get("environmentErrorCount", 0)),
            },
        }
        # TODO: replace these heuristics with LLM-guided RCA once prompt-grounded
        # reasoning can consume DOM history, OCR evidence, and run diffs safely.
        self.log_end(result)
        return result
