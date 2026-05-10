from __future__ import annotations

import re
from typing import Any


class TestCoverageAnalyzer:
    """Identify UI coverage gaps from bundle and prior phase outputs."""

    def analyze(
        self,
        bundle: dict[str, Any],
        risk_report: dict[str, Any],
        agent_output: dict[str, Any],
        autofix_output: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        steps = bundle.get("steps") or []
        executed_labels = {
            str(label).strip()
            for step in steps
            for label in (step.get("labels") or [])
            if str(label).strip()
        }
        executed_step_names = {
            str(step.get("stepName") or "").strip().lower()
            for step in steps
            if str(step.get("stepName") or "").strip()
        }

        visible_labels = self._extract_visible_labels(bundle.get("ocrText", ""))
        missing_fields = [label for label in visible_labels if label not in executed_labels]

        missing_actions: list[str] = []
        if "go" in {label.lower() for label in visible_labels} and not self._contains_action(executed_step_names, "go"):
            missing_actions.append("Go button not clicked")
        if "search" in {label.lower() for label in visible_labels} and not self._contains_action(executed_step_names, "search"):
            missing_actions.append("Search action not executed")

        high_risk_screens = self._high_risk_screens(bundle, risk_report, agent_output)
        skipped_flows = self._skipped_flows(steps, visible_labels)

        return {
            "missingFields": missing_fields,
            "missingActions": missing_actions,
            "highRiskScreens": high_risk_screens,
            "skippedFlows": skipped_flows,
            "autofixSignals": self._autofix_signals(autofix_output),
        }

    def _extract_visible_labels(self, ocr_text: str) -> list[str]:
        labels: list[str] = []
        for raw_line in str(ocr_text or "").splitlines():
            line = raw_line.strip()
            if len(line) < 3:
                continue
            if re.search(r"^[A-Za-z][A-Za-z0-9 /_-]{2,}$", line):
                labels.append(line[:120])
        return self._ordered_unique(labels)

    def _contains_action(self, executed_step_names: set[str], action: str) -> bool:
        return any(action in step_name for step_name in executed_step_names)

    def _high_risk_screens(
        self,
        bundle: dict[str, Any],
        risk_report: dict[str, Any],
        agent_output: dict[str, Any],
    ) -> list[str]:
        screens: list[str] = []
        ui_context = (
            agent_output.get("agents", {}).get("testReader", {}).get("uiContext")
            or agent_output.get("uiContext")
            or bundle.get("testName")
            or "Unknown screen"
        )
        if risk_report.get("riskLevel") in {"HIGH", "MEDIUM"}:
            screens.append(str(ui_context))
        if "HIGH" == agent_output.get("finalReport", {}).get("riskLevel"):
            screens.append(str(ui_context))
        return self._ordered_unique(screens)

    def _skipped_flows(self, steps: list[dict[str, Any]], visible_labels: list[str]) -> list[str]:
        if not steps:
            return []
        failing_index = len(steps) - 1
        for index, step in enumerate(steps):
            if str(step.get("errorMessage") or "").strip():
                failing_index = index
                break
        if failing_index >= len(steps) - 1:
            trailing_labels = [
                label for label in visible_labels
                if label.lower() not in {str(step.get("stepName") or "").lower() for step in steps}
            ]
            return [f"Potential flow after failure not covered: {label}" for label in trailing_labels[:3]]
        return [
            f"Steps after index {failing_index} were skipped due to early failure"
        ]

    def _autofix_signals(self, autofix_output: dict[str, Any] | None) -> list[str]:
        if not autofix_output:
            return []
        signals: list[str] = []
        for fix in autofix_output.get("fixes", []):
            signals.append(fix.get("fixType", "unknown"))
        return self._ordered_unique([str(signal) for signal in signals if signal])

    def _ordered_unique(self, items: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result
