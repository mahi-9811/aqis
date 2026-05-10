from __future__ import annotations

from typing import Any

from aqis.agents.base_agent import BaseAgent


class FixSuggestionAgent(BaseAgent):
    """Generate deterministic remediation candidates from failure categories."""

    agent_name = "fix_suggestion"

    RULES: dict[str, list[str]] = {
        "PAGE_LOAD_TIMING": [
            "Add WAITUNTIL PageReady before interacting with the target page",
            "Wait for the stable page header or shell container before scanning",
        ],
        "LOCATOR_NOT_FOUND": [
            "Replace dynamic XPath with a stable ID-based locator",
            "Scope the locator to a stable parent container before interaction",
        ],
        "FLAKY_TEST": [
            "Add retry plus deterministic synchronization around the failing step",
            "Stabilize the test by waiting for the UI state transition instead of timing guesses",
        ],
        "ENVIRONMENT_INSTABILITY": [
            "Run environment health checks before executing the scenario",
            "Verify SAP UI5 backend availability and clear transient environment faults",
        ],
        "UNKNOWN_FAILURE": [
            "Collect additional DOM and OCR evidence before changing the test logic",
        ],
    }

    def run(self, bundle: dict[str, Any], previous_output: dict[str, Any] | None = None) -> dict[str, Any]:
        self.validate_bundle(bundle)
        self.log_start(bundle)

        categories = list((previous_output or {}).get("failureCategories") or [])
        fixes: list[str] = []
        for category in categories or ["UNKNOWN_FAILURE"]:
            fixes.extend(self.RULES.get(category, self.RULES["UNKNOWN_FAILURE"]))

        result = {
            "fixes": self.unique_ordered(fixes),
        }
        # TODO: let an LLM produce context-aware fix drafts constrained by safe
        # coding/test-automation policy rules.
        self.log_end(result)
        return result
