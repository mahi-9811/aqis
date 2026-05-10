from __future__ import annotations

from typing import Any


class TestScenarioGenerator:
    """Generate preventive scenario descriptions from RCA and coverage gaps."""

    def generate(
        self,
        bundle: dict[str, Any],
        risk_report: dict[str, Any],
        agent_output: dict[str, Any],
        coverage_report: dict[str, Any],
        autofix_output: dict[str, Any] | None = None,
    ) -> list[dict[str, str]]:
        categories = list(
            agent_output.get("agents", {}).get("failureAnalyzer", {}).get("failureCategories")
            or agent_output.get("failureCategories")
            or []
        )

        scenarios: list[dict[str, str]] = []
        if "LOCATOR_NOT_FOUND" in categories:
            scenarios.append(
                {
                    "scenarioName": "Verify locator stability for critical field",
                    "description": "Ensure the primary locator remains stable across UI refreshes and dynamic layout updates",
                    "testType": "STABILITY",
                    "priority": "HIGH",
                }
            )
        if "PAGE_LOAD_TIMING" in categories:
            scenarios.append(
                {
                    "scenarioName": "Verify dynamic page header loads correctly",
                    "description": "Ensure header and page shell are rendered before interaction begins",
                    "testType": "STABILITY",
                    "priority": "HIGH",
                }
            )
        if "FLAKY_TEST" in categories:
            scenarios.append(
                {
                    "scenarioName": "Verify repeated execution remains stable",
                    "description": "Run the scenario under repeated execution to confirm bounded retry logic is not masking instability",
                    "testType": "RESILIENCE",
                    "priority": "HIGH",
                }
            )

        for field in coverage_report.get("missingFields", []):
            scenarios.append(
                {
                    "scenarioName": f"Validate coverage for {field}",
                    "description": f"Interact with the {field} field and verify expected behavior and validation rules",
                    "testType": "FUNCTIONAL",
                    "priority": "MEDIUM",
                }
            )

        for action in coverage_report.get("missingActions", []):
            scenarios.append(
                {
                    "scenarioName": f"Cover missing action: {action}",
                    "description": f"Add a preventive test to exercise the skipped action '{action}' before the next release",
                    "testType": "FUNCTIONAL",
                    "priority": "MEDIUM",
                }
            )

        if risk_report.get("riskLevel") == "HIGH":
            scenarios.append(
                {
                    "scenarioName": "Verify high-risk screen before release",
                    "description": "Exercise all critical interactions on the identified high-risk screen before the next scheduled run",
                    "testType": "RISK_BASED",
                    "priority": "HIGH",
                }
            )

        if autofix_output and autofix_output.get("recommended"):
            scenarios.append(
                {
                    "scenarioName": "Validate proposed self-healing fix",
                    "description": "Confirm the recommended AutoFix improves stability without changing functional behavior",
                    "testType": "REGRESSION",
                    "priority": "MEDIUM",
                }
            )

        return self._ordered_unique(scenarios)

    def _ordered_unique(self, scenarios: list[dict[str, str]]) -> list[dict[str, str]]:
        seen: set[tuple[str, str]] = set()
        result: list[dict[str, str]] = []
        for scenario in scenarios:
            key = (scenario["scenarioName"], scenario["testType"])
            if key not in seen:
                seen.add(key)
                result.append(scenario)
        return result
