from __future__ import annotations

from typing import Any

from aqis.autofix.base_fix import BaseFix
from aqis.risk_engine.feature_extractor import extract_features


class PreconditionGenerator(BaseFix):
    """Generate setup and navigation guards before the failing step."""

    fix_type = "precondition"
    description = "Generate pre-condition checks"

    def apply(self, bundle: dict[str, Any], agent_output: dict[str, Any]) -> dict[str, Any]:
        self.validate_bundle(bundle)
        self.validate_agent_output(agent_output)
        step = self.affected_step(bundle)
        preconditions = self.generate_preconditions(bundle, agent_output)
        confidence = 0.38 + (0.12 if preconditions else 0.0)
        return self.build_fix(
            description="Generated pre-condition recommendations",
            confidence=confidence,
            step_name=str(step.get("stepName", "Unknown step")),
            payload={"preconditions": preconditions},
            patch_hint=preconditions[0] if preconditions else "",
        )

    def generate_preconditions(self, bundle: dict[str, Any], agent_output: dict[str, Any]) -> list[str]:
        features = extract_features(bundle)
        preconditions: list[str] = []

        ui_context = self._ui_context(agent_output, bundle)
        ocr_text = str(bundle.get("ocrText") or "").lower()
        if bool(features.get("screenNotReady", 0)):
            preconditions.append(f"Ensure user is on '{ui_context}' page before interacting")
            preconditions.append("Verify the page shell and header are fully loaded before scanning")

        if "modal" in ocr_text or "dialog" in ocr_text or "popup" in ocr_text:
            preconditions.append("Close any blocking modal dialogs before continuing")

        if int(features.get("environmentErrorCount", 0)) > 0:
            preconditions.append("Verify environment health and backend connectivity before execution")

        return self._dedupe(preconditions)

    def _ui_context(self, agent_output: dict[str, Any], bundle: dict[str, Any]) -> str:
        if "uiContext" in agent_output:
            return str(agent_output.get("uiContext") or bundle.get("testName") or "Target page")
        return str(
            agent_output.get("agents", {}).get("testReader", {}).get("uiContext")
            or bundle.get("testName")
            or "Target page"
        )

    def _dedupe(self, items: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result
