from typing import Any, Dict
import re
import xml.etree.ElementTree as ET


XML_DECLARATION_RE = re.compile(br"^\s*<\?xml[^>]*\?>", re.IGNORECASE)


def _parse_root(xml_bytes: bytes) -> ET.Element:
    try:
        return ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        message = str(exc).lower()
        if "encoding specified in xml declaration is incorrect" not in message:
            raise

    # Retry without the XML declaration when the bytes and declared encoding disagree.
    sanitized = XML_DECLARATION_RE.sub(b"", xml_bytes, count=1)
    return ET.fromstring(sanitized)


def parse_xml(xml_bytes: bytes) -> Dict[str, Any]:
    """
    Parse log.xml and extract test details.

    Args:
        xml_bytes (bytes): The content of the log.xml file.

    Returns:
        dict: Extracted data including test name, steps, timings, labels, and error messages.
    """
    try:
        root = _parse_root(xml_bytes)
        test_name = root.findtext("TestName", default="")
        steps = [
            {
                "stepName": step.findtext("StepName", default=""),
                "executedProperty": step.findtext("ExecutedProperty", default=""),
                "timing": step.findtext("Timing", default=""),
                "labels": [label.text for label in step.findall("Label")],
                "errorMessage": step.findtext("ErrorMessage", default=""),
            }
            for step in root.findall("Step")
        ]
        return {
            "testName": test_name,
            "steps": steps,
            "timings": [step["timing"] for step in steps],
            "labels": [label for step in steps for label in step["labels"]],
        }
    except ET.ParseError as e:
        # Gracefully handle XML parsing errors
        return {"error": f"Failed to parse XML: {str(e)}"}
