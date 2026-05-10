from __future__ import annotations

from typing import Any

from aqis.autofix.base_fix import BaseFix


class WaitStrategyGenerator(BaseFix):
    """Recommend synchronization primitives without using hard sleeps."""

    fix_type = "wait"
    description = "Generate safe WAITUNTIL strategies"

    def apply(self, bundle: dict[str, Any], agent_output: dict[str, Any]) -> dict[str, Any]:
        self.validate_bundle(bundle)
        self.validate_agent_output(agent_output)
        step = self.affected_step(bundle)
        waits = self.generate_waits(bundle, agent_output)
        confidence = 0.4 + (0.15 if waits else 0.0)
        return self.build_fix(
            description="Generated synchronization recommendations",
            confidence=confidence,
            step_name=str(step.get("stepName", "Unknown step")),
            payload={"waits": waits},
            patch_hint=waits[0] if waits else "",
        )

    def generate_waits(self, bundle: dict[str, Any], agent_output: dict[str, Any]) -> list[str]:
        failure_categories = self._extract_categories(agent_output)
        ui_context = self._extract_ui_context(agent_output, bundle)
        step = self.affected_step(bundle)
        labels = step.get("labels") or []
        element_name = str(labels[0] if labels else step.get("stepName") or "Target element").strip()

        waits: list[str] = []
        if "PAGE_LOAD_TIMING" in failure_categories:
            waits.append(f"WAITUNTIL PageReady('{ui_context}')")
        if "LOCATOR_NOT_FOUND" in failure_categories:
            waits.append(f"WAITUNTIL ElementVisible('{element_name}')")
        if "FLAKY_TEST" in failure_categories:
            waits.append(f"WAITUNTIL ElementVisible('{element_name}')")
            waits.append("Retry action with bounded retry count after readiness confirmation")
        return self._dedupe(waits)

    def _extract_categories(self, agent_output: dict[str, Any]) -> list[str]:
        if "failureCategories" in agent_output:
            return list(agent_output.get("failureCategories") or [])
        failure = agent_output.get("agents", {}).get("failureAnalyzer", {})
        return list(failure.get("failureCategories") or [])

    def _extract_ui_context(self, agent_output: dict[str, Any], bundle: dict[str, Any]) -> str:
        if "uiContext" in agent_output:
            return str(agent_output.get("uiContext") or bundle.get("testName") or "Target page")
        reader = agent_output.get("agents", {}).get("testReader", {})
        return str(reader.get("uiContext") or bundle.get("testName") or "Target page")

    def _dedupe(self, items: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result
