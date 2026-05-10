from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from aqis.core.logger import setup_logger


class BaseFix(ABC):
    """Shared base class for deterministic autofix generators."""

    fix_type: str = "base"
    confidence: float = 0.0
    description: str = ""

    def __init__(self) -> None:
        self.logger = setup_logger(f"aqis.autofix.{self.fix_type}")

    @abstractmethod
    def apply(self, bundle: dict[str, Any], agent_output: dict[str, Any]) -> dict[str, Any]:
        """
        Produce a structured autofix payload.

        TODO: plug in constrained LLM reasoning after deterministic safety
        checks remain the first gate on all generated changes.
        """

    def validate_bundle(self, bundle: dict[str, Any]) -> None:
        if not isinstance(bundle, dict):
            raise TypeError("bundle must be a dictionary")
        if not bundle.get("testName"):
            raise ValueError("bundle must include testName")

    def validate_agent_output(self, agent_output: dict[str, Any]) -> None:
        if not isinstance(agent_output, dict):
            raise TypeError("agent_output must be a dictionary")

    def rollback_safe(self, fix: dict[str, Any]) -> bool:
        """Only allow localized, human-reviewable changes."""
        patch = str(fix.get("patchHint", ""))
        if "sleep" in patch.lower():
            return False
        return True

    def affected_step(self, bundle: dict[str, Any]) -> dict[str, Any]:
        for index, step in enumerate(bundle.get("steps") or []):
            if str(step.get("errorMessage") or "").strip():
                step_copy = dict(step)
                step_copy["_index"] = index
                return step_copy
        steps = bundle.get("steps") or []
        if steps:
            step_copy = dict(steps[-1])
            step_copy["_index"] = len(steps) - 1
            return step_copy
        return {"stepName": "Unknown step", "_index": 0}

    def build_fix(
        self,
        *,
        description: str,
        confidence: float,
        step_name: str,
        payload: dict[str, Any],
        patch_hint: str = "",
    ) -> dict[str, Any]:
        return {
            "fixType": self.fix_type,
            "description": description,
            "confidence": round(max(0.0, min(1.0, confidence)), 2),
            "affectedStep": step_name,
            "rollbackSafe": self.rollback_safe({"patchHint": patch_hint}),
            **payload,
            "patchHint": patch_hint,
        }
