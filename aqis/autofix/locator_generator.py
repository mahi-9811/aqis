from __future__ import annotations

import re
from typing import Any

from aqis.autofix.base_fix import BaseFix


class LocatorGenerator(BaseFix):
    """Generate safer locator alternatives from bundle evidence."""

    fix_type = "locator"
    description = "Generate stable locator candidates"

    def apply(self, bundle: dict[str, Any], agent_output: dict[str, Any]) -> dict[str, Any]:
        self.validate_bundle(bundle)
        self.validate_agent_output(agent_output)
        step = self.affected_step(bundle)
        locators = self.generate_locators(bundle)
        confidence = 0.35 + (0.2 if any(item["locatorType"] == "ID" for item in locators) else 0.0)
        return self.build_fix(
            description="Generated stable locator alternatives",
            confidence=confidence,
            step_name=str(step.get("stepName", "Unknown step")),
            payload={"locators": locators},
            patch_hint=locators[0]["locatorValue"] if locators else "",
        )

    def generate_locators(self, bundle: dict[str, Any]) -> list[dict[str, str]]:
        step = self.affected_step(bundle)
        executed_property = str(step.get("executedProperty") or "")
        labels = step.get("labels") or []
        field_label = str(labels[0] if labels else step.get("stepName") or "").strip()
        ocr_text = str(bundle.get("ocrText") or "").strip()

        candidates: list[dict[str, str]] = []

        id_value = self._extract_id(executed_property)
        if id_value:
            candidates.append(
                {
                    "locatorType": "ID",
                    "locatorValue": id_value,
                    "reason": "More stable than dynamic class-based XPath",
                }
            )

        aria_value = field_label or self._first_ocr_phrase(ocr_text)
        if aria_value:
            candidates.append(
                {
                    "locatorType": "ARIA_LABEL",
                    "locatorValue": aria_value,
                    "reason": "Derived from visible UI text and likely more stable than structural selectors",
                }
            )

        text_value = self._first_ocr_phrase(ocr_text)
        if text_value:
            candidates.append(
                {
                    "locatorType": "VISIBLE_TEXT",
                    "locatorValue": text_value,
                    "reason": "Can anchor the element through visible text when ID metadata is absent",
                }
            )

        xpath_value = self._sanitize_xpath(executed_property)
        if xpath_value:
            candidates.append(
                {
                    "locatorType": "XPATH",
                    "locatorValue": xpath_value,
                    "reason": "Fallback only after rejecting brittle absolute XPath expressions",
                }
            )

        return self._dedupe(candidates)

    def _extract_id(self, executed_property: str) -> str:
        match = re.search(r"(?:id=|ID\(|@id=['\"])([A-Za-z0-9_:\-.]+)", executed_property)
        if match:
            return match.group(1)
        return ""

    def _sanitize_xpath(self, executed_property: str) -> str:
        if "xpath" not in executed_property.lower() and not executed_property.strip().startswith("//"):
            return ""
        match = re.search(r"(//.*)", executed_property)
        xpath = match.group(1) if match else executed_property.strip()
        if xpath.startswith("/html") or xpath.startswith("/body") or xpath.startswith("(/html"):
            return ""
        if xpath.count("/") > 8 and "@id" not in xpath and "text()" not in xpath:
            return ""
        return xpath

    def _first_ocr_phrase(self, ocr_text: str) -> str:
        for line in ocr_text.splitlines():
            cleaned = line.strip()
            if len(cleaned) >= 3:
                return cleaned[:120]
        return ""

    def _dedupe(self, candidates: list[dict[str, str]]) -> list[dict[str, str]]:
        seen: set[tuple[str, str]] = set()
        result: list[dict[str, str]] = []
        for item in candidates:
            key = (item["locatorType"], item["locatorValue"])
            if item["locatorValue"] and key not in seen:
                seen.add(key)
                result.append(item)
        return result
