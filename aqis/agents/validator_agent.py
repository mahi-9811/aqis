from __future__ import annotations

from typing import Any

from aqis.agents.base_agent import BaseAgent


class ValidationAgent(BaseAgent):
    """Reject unsafe remediations and score confidence in the remaining set."""

    agent_name = "validation"

    def run(self, bundle: dict[str, Any], previous_output: dict[str, Any] | None = None) -> dict[str, Any]:
        self.validate_bundle(bundle)
        self.log_start(bundle)

        candidate_fixes = list((previous_output or {}).get("fixes") or [])
        approved_fixes: list[str] = []
        rejected_fixes: list[str] = []
        ocr_text = self.safe_text(bundle.get("ocrText")).lower()
        steps = bundle.get("steps") or []
        executed_properties = " ".join(self.safe_text(step.get("executedProperty")).lower() for step in steps)

        for fix in candidate_fixes:
            normalized = fix.lower()
            if "sleep" in normalized and "waituntil" not in normalized:
                rejected_fixes.append(fix)
                continue
            if "xpath" in normalized and "id-based" not in normalized and "stable parent" not in normalized:
                rejected_fixes.append(fix)
                continue
            if "locator" in normalized and ocr_text and not self._locator_has_ui_context(ocr_text, executed_properties):
                rejected_fixes.append(fix)
                continue
            approved_fixes.append(fix)

        confidence = self._compute_confidence(approved_fixes, rejected_fixes, bundle)
        result = {
            "fixApproved": bool(approved_fixes),
            "confidenceScore": confidence,
            "approvedFixes": approved_fixes,
            "rejectedFixes": rejected_fixes,
        }
        # TODO: add verifier prompts that compare proposed fixes to DOM/OCR evidence.
        self.log_end(result)
        return result

    def _locator_has_ui_context(self, ocr_text: str, executed_properties: str) -> bool:
        if executed_properties:
            tokens = [token for token in executed_properties.replace("=", " ").split() if len(token) > 2]
            return any(token.lower() in ocr_text for token in tokens[:5])
        return bool(ocr_text)

    def _compute_confidence(
        self,
        approved_fixes: list[str],
        rejected_fixes: list[str],
        bundle: dict[str, Any],
    ) -> float:
        score = 0.5
        if approved_fixes:
            score += 0.25
        if bundle.get("ocrText"):
            score += 0.1
        if bundle.get("steps"):
            score += 0.1
        if rejected_fixes:
            score -= min(0.2, 0.05 * len(rejected_fixes))
        return round(max(0.0, min(1.0, score)), 2)
