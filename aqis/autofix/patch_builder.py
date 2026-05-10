from __future__ import annotations

from typing import Any


class PatchBuilder:
    """Render autofix suggestions into a human-readable patch-like diff."""

    def build_patch(self, bundle: dict[str, Any], fixes: list[dict[str, Any]]) -> str:
        step = self._affected_step(bundle)
        before_locator = str(step.get("executedProperty") or "UNSPECIFIED_LOCATOR")
        lines = ["--- BEFORE", "+++ AFTER", f"- findBy {before_locator}"]

        for fix in fixes:
            if fix.get("fixType") == "locator":
                for locator in fix.get("locators", []):
                    lines.append(
                        f"+ findBy {locator['locatorType']}(\"{locator['locatorValue']}\")"
                    )
            if fix.get("fixType") == "wait":
                for wait in fix.get("waits", []):
                    lines.append(f"+ {wait}")
            if fix.get("fixType") == "precondition":
                for condition in fix.get("preconditions", []):
                    lines.append(f"+ PRECONDITION {condition}")

        return "\n".join(lines)

    def _affected_step(self, bundle: dict[str, Any]) -> dict[str, Any]:
        for step in bundle.get("steps") or []:
            if str(step.get("errorMessage") or "").strip():
                return step
        steps = bundle.get("steps") or []
        if steps:
            return steps[-1]
        return {}
