from __future__ import annotations

from typing import Any

from aqis.autofix.locator_generator import LocatorGenerator
from aqis.autofix.patch_builder import PatchBuilder
from aqis.autofix.precondition_generator import PreconditionGenerator
from aqis.autofix.wait_strategy import WaitStrategyGenerator


def generate_autofix(bundle: dict[str, Any], agent_output: dict[str, Any]) -> dict[str, Any]:
    """Generate safe deterministic autofix recommendations from bundle + RCA."""
    locator_generator = LocatorGenerator()
    wait_generator = WaitStrategyGenerator()
    precondition_generator = PreconditionGenerator()
    patch_builder = PatchBuilder()

    locator_fix = locator_generator.apply(bundle, agent_output)
    wait_fix = wait_generator.apply(bundle, agent_output)
    precondition_fix = precondition_generator.apply(bundle, agent_output)

    candidate_fixes = [locator_fix, wait_fix, precondition_fix]
    safe_fixes = [
        fix for fix in candidate_fixes
        if fix.get("rollbackSafe", False) and _has_actionable_payload(fix)
    ]
    confidence = _score_confidence(safe_fixes, agent_output)
    patch = patch_builder.build_patch(bundle, safe_fixes)

    return {
        "fixes": safe_fixes,
        "patch": patch,
        "confidence": confidence,
        "recommended": bool(safe_fixes and confidence >= 0.55),
    }


def _has_actionable_payload(fix: dict[str, Any]) -> bool:
    return bool(
        fix.get("locators")
        or fix.get("waits")
        or fix.get("preconditions")
    )


def _score_confidence(fixes: list[dict[str, Any]], agent_output: dict[str, Any]) -> float:
    if not fixes:
        return 0.0

    average = sum(float(fix.get("confidence", 0.0)) for fix in fixes) / len(fixes)
    bonus = 0.0
    categories = list(
        agent_output.get("failureCategories")
        or agent_output.get("agents", {}).get("failureAnalyzer", {}).get("failureCategories")
        or []
    )
    if "LOCATOR_NOT_FOUND" in categories:
        bonus += 0.1
    if "PAGE_LOAD_TIMING" in categories:
        bonus += 0.08
    if agent_output.get("historicalInsights") or agent_output.get("agents", {}).get("contextRetriever", {}).get("historicalInsights"):
        bonus += 0.05

    return round(max(0.0, min(1.0, average + bonus)), 2)
