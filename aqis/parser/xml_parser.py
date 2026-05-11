from typing import Any, Dict
import re
import xml.etree.ElementTree as ET


XML_DECLARATION_RE = re.compile(br"^\s*<\?xml[^>]*\?>", re.IGNORECASE)

# Invalid XML 1.0 characters (control chars except tab/newline/carriage-return)
_INVALID_XML_CHARS_RE = re.compile(
    rb"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"
)


def _sanitize(xml_bytes: bytes) -> bytes:
    """Strip invalid XML 1.0 control characters and fix common encoding issues."""
    # Remove invalid control characters
    xml_bytes = _INVALID_XML_CHARS_RE.sub(b"", xml_bytes)
    # Escape bare & that are not already part of an entity reference
    xml_bytes = re.sub(rb"&(?!(?:[a-zA-Z][a-zA-Z0-9]*|#[0-9]+|#x[0-9a-fA-F]+);)", b"&amp;", xml_bytes)
    return xml_bytes


def _parse_root(xml_bytes: bytes) -> ET.Element:
    try:
        return ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        message = str(exc).lower()
        # Retry without XML declaration when encoding declared disagrees with bytes
        if "encoding specified in xml declaration is incorrect" in message:
            xml_bytes = XML_DECLARATION_RE.sub(b"", xml_bytes, count=1)
            try:
                return ET.fromstring(xml_bytes)
            except ET.ParseError:
                pass

    # Retry after sanitizing invalid characters and bare ampersands
    sanitized = _sanitize(xml_bytes)
    sanitized = XML_DECLARATION_RE.sub(b"", sanitized, count=1)
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
