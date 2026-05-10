from __future__ import annotations

import re
from typing import Any


class NegativeTestGenerator:
    """Generate negative and boundary test ideas from visible fields and steps."""

    def generate(self, bundle: dict[str, Any], coverage_report: dict[str, Any]) -> list[dict[str, str]]:
        scenarios: list[dict[str, str]] = []
        labels = set(coverage_report.get("missingFields", []))
        for step in bundle.get("steps") or []:
            for label in (step.get("labels") or []):
                if str(label).strip():
                    labels.add(str(label).strip())

        for label in sorted(labels):
            scenarios.append(
                {
                    "scenario": f"Submit without {label} value",
                    "expected": "Validation error shown",
                }
            )
            if re.search(r"(id|number|quotation|reference)", label, re.IGNORECASE):
                scenarios.append(
                    {
                        "scenario": f"Enter invalid format into {label}",
                        "expected": "Inline validation blocks invalid value",
                    }
                )

        if bundle.get("ocrText"):
            scenarios.append(
                {
                    "scenario": "Attempt interaction before page ready",
                    "expected": "UI blocks interaction until page is fully loaded",
                }
            )

        return self._ordered_unique(scenarios)

    def _ordered_unique(self, scenarios: list[dict[str, str]]) -> list[dict[str, str]]:
        seen: set[tuple[str, str]] = set()
        result: list[dict[str, str]] = []
        for scenario in scenarios:
            key = (scenario["scenario"], scenario["expected"])
            if key not in seen:
                seen.add(key)
                result.append(scenario)
        return result
