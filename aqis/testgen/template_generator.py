from __future__ import annotations

from typing import Any


class AutomationTemplateGenerator:
    """Render scenarios into lightweight automation guidance templates."""

    def generate(
        self,
        bundle: dict[str, Any],
        scenarios: list[dict[str, str]],
        negative_tests: list[dict[str, str]],
    ) -> dict[str, str]:
        context = bundle.get("testName") or "Target page"
        selenium = self._selenium_template(context, scenarios)
        playwright = self._playwright_template(context, scenarios)
        bdd = self._bdd_template(context, scenarios, negative_tests)
        combined = "\n\n".join(
            [
                "### Selenium",
                selenium,
                "### Playwright",
                playwright,
                "### Gherkin",
                bdd,
            ]
        )
        return {
            "selenium": selenium,
            "playwright": playwright,
            "gherkin": bdd,
            "automationTemplates": combined,
        }

    def _selenium_template(self, context: str, scenarios: list[dict[str, str]]) -> str:
        lines = [f"// Selenium pseudo-template for {context}"]
        for scenario in scenarios[:3]:
            lines.extend(
                [
                    f"// Scenario: {scenario['scenarioName']}",
                    "driver.navigate().to(<target-url>);",
                    "waitUntilPageReady();",
                    "performPrimaryInteraction();",
                    "verifyExpectedOutcome();",
                ]
            )
        return "\n".join(lines)

    def _playwright_template(self, context: str, scenarios: list[dict[str, str]]) -> str:
        lines = [f"// Playwright pseudo-template for {context}"]
        for scenario in scenarios[:3]:
            lines.extend(
                [
                    f"// Scenario: {scenario['scenarioName']}",
                    "await page.goto('<target-url>');",
                    "await expect(page.locator('<page-ready-selector>')).toBeVisible();",
                    "await page.locator('<primary-selector>').click();",
                    "await expect(page.locator('<assertion-selector>')).toBeVisible();",
                ]
            )
        return "\n".join(lines)

    def _bdd_template(
        self,
        context: str,
        scenarios: list[dict[str, str]],
        negative_tests: list[dict[str, str]],
    ) -> str:
        lines = [f"Feature: Preventive coverage for {context}"]
        for scenario in scenarios[:2]:
            lines.extend(
                [
                    "",
                    f"Scenario: {scenario['scenarioName']}",
                    f"  Given user is on {context}",
                    "  When user performs the protected interaction",
                    "  Then the UI remains stable and expected results are shown",
                ]
            )
        if negative_tests:
            lines.extend(
                [
                    "",
                    f"Scenario: {negative_tests[0]['scenario']}",
                    f"  Given user is on {context}",
                    "  When user submits invalid or incomplete data",
                    f"  Then {negative_tests[0]['expected']}",
                ]
            )
        return "\n".join(lines)
