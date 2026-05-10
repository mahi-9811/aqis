from __future__ import annotations

from typing import Any

from aqis.testgen.coverage_analyzer import TestCoverageAnalyzer
from aqis.testgen.negative_generator import NegativeTestGenerator
from aqis.testgen.scenario_generator import TestScenarioGenerator
from aqis.testgen.template_generator import AutomationTemplateGenerator


def generate_test_cases(
    bundle: dict[str, Any],
    risk_report: dict[str, Any],
    agent_output: dict[str, Any],
    autofix_output: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate deterministic preventive test cases and guidance templates."""
    coverage_analyzer = TestCoverageAnalyzer()
    scenario_generator = TestScenarioGenerator()
    negative_generator = NegativeTestGenerator()
    template_generator = AutomationTemplateGenerator()

    coverage_report = coverage_analyzer.analyze(bundle, risk_report, agent_output, autofix_output)
    scenarios = scenario_generator.generate(bundle, risk_report, agent_output, coverage_report, autofix_output)
    negative_tests = negative_generator.generate(bundle, coverage_report)
    templates = template_generator.generate(bundle, scenarios, negative_tests)

    ranked_tests = _rank_by_priority(scenarios, negative_tests, risk_report)
    return {
        "coverageAnalysis": coverage_report,
        "generatedTests": ranked_tests,
        "priorityOrder": ["HIGH", "MEDIUM", "LOW"],
        "recommendation": _recommendation(risk_report, ranked_tests),
        "automationTemplates": templates,
        # TODO: augment this with LLM-generated scenario diversification once
        # deterministic safety filters and ranking remain authoritative.
    }


def _rank_by_priority(
    scenarios: list[dict[str, str]],
    negative_tests: list[dict[str, str]],
    risk_report: dict[str, Any],
) -> list[dict[str, str]]:
    ranked: list[dict[str, str]] = []
    for scenario in scenarios:
        ranked.append(
            {
                "name": scenario["scenarioName"],
                "description": scenario["description"],
                "type": scenario["testType"],
                "priority": scenario["priority"],
            }
        )
    for negative in negative_tests[:4]:
        ranked.append(
            {
                "name": negative["scenario"],
                "description": negative["expected"],
                "type": "NEGATIVE",
                "priority": "HIGH" if risk_report.get("riskLevel") == "HIGH" else "MEDIUM",
            }
        )
    priority_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    ranked.sort(key=lambda item: (priority_rank.get(item["priority"], 3), item["name"]))
    return ranked


def _recommendation(risk_report: dict[str, Any], ranked_tests: list[dict[str, str]]) -> str:
    if not ranked_tests:
        return "No additional preventive tests generated"
    if risk_report.get("riskLevel") == "HIGH":
        return "Add HIGH priority tests before next run"
    if risk_report.get("riskLevel") == "MEDIUM":
        return "Add HIGH and MEDIUM priority tests before the next release cycle"
    return "Add MEDIUM priority preventive tests as backlog hardening work"
