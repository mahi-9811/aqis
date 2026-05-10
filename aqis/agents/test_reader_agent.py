from __future__ import annotations

from typing import Any

from aqis.agents.base_agent import BaseAgent


class TestReaderAgent(BaseAgent):
    """Extract a concise test-intent summary from the normalized bundle."""

    agent_name = "test_reader"
    __test__ = False

    def run(self, bundle: dict[str, Any], previous_output: dict[str, Any] | None = None) -> dict[str, Any]:
        self.validate_bundle(bundle)
        self.log_start(bundle)

        steps = bundle.get("steps") or []
        failing_step = self._select_focus_step(steps)
        step_name = self.safe_text(failing_step.get("stepName")) or "Unknown step"
        step_index = int(failing_step.get("_index", 0))
        labels = failing_step.get("labels") or []
        field_label = self.safe_text(labels[0] if labels else step_name)
        field_value = self.safe_text(
            failing_step.get("fieldValue")
            or failing_step.get("executedProperty")
            or failing_step.get("value")
        )
        locator_type = self._infer_locator_type(
            self.safe_text(
                failing_step.get("locatorType")
                or failing_step.get("locator")
                or failing_step.get("executedProperty")
            )
        )

        result = {
            "testIntent": self._derive_test_intent(bundle.get("testName", ""), step_name, field_label),
            "uiContext": self._derive_ui_context(bundle, step_name),
            "stepSummary": self._derive_step_summary(step_name, field_label, field_value),
            "stepName": step_name,
            "stepIndex": step_index,
            "fieldLabel": field_label,
            "fieldValue": field_value,
            "locatorType": locator_type,
        }
        self.log_end(result)
        return result

    def _select_focus_step(self, steps: list[dict[str, Any]]) -> dict[str, Any]:
        indexed_steps = []
        for index, step in enumerate(steps):
            current = dict(step)
            current["_index"] = index
            indexed_steps.append(current)

        for step in indexed_steps:
            error_message = self.safe_text(step.get("errorMessage")).lower()
            if error_message:
                return step

        if indexed_steps:
            return indexed_steps[-1]
        return {"stepName": "Unknown step", "_index": 0}

    def _derive_test_intent(self, test_name: str, step_name: str, field_label: str) -> str:
        raw = test_name or step_name or field_label or "Unknown test"
        tokens = raw.replace("_", " ").replace("-", " ").split()
        if not tokens:
            return "Unknown test intent"
        return " ".join(token.capitalize() for token in tokens)

    def _derive_ui_context(self, bundle: dict[str, Any], step_name: str) -> str:
        ocr_text = self.safe_text(bundle.get("ocrText"))
        if ocr_text:
            first_line = ocr_text.splitlines()[0].strip()
            if first_line:
                return first_line[:120]
        test_name = self.safe_text(bundle.get("testName"))
        if test_name:
            return f"UI flow for {test_name}"
        return f"UI flow around {step_name}"

    def _derive_step_summary(self, step_name: str, field_label: str, field_value: str) -> str:
        if field_value:
            return f"{step_name} using {field_label} = {field_value}"
        if field_label and field_label != step_name:
            return f"{step_name} for {field_label}"
        return step_name

    def _infer_locator_type(self, locator_value: str) -> str:
        value = locator_value.lower()
        if "xpath" in value or value.startswith("//"):
            return "XPATH"
        if "id" in value:
            return "ID"
        if "css" in value:
            return "CSS"
        if "name" in value:
            return "NAME"
        return "UNKNOWN"
