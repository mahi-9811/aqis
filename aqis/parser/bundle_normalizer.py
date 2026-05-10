from typing import Any, Dict


def build_failure_bundle(
    xml_data: Dict[str, Any], startlog_data: Dict[str, Any], ocr_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Normalize and merge extracted data into a unified failure bundle.

    Args:
        xml_data (dict): Parsed data from log.xml.
        startlog_data (dict): Parsed data from STARTLog.txt.
        ocr_data (dict): Extracted OCR data from screenshots.

    Returns:
        dict: Unified failure bundle.
    """
    return {
        "testName": xml_data.get("testName", ""),
        "steps": xml_data.get("steps", []),
        "exception": startlog_data.get("exceptions", []),
        "retries": startlog_data.get("retries", 0),
        "autoHeal": startlog_data.get("autoHeal", {}),
        "driftSignals": startlog_data.get("driftSignals", {}),
        "timingSignals": xml_data.get("timings", []),
        "ocrText": ocr_data.get("ocrText", ""),
        "raw": {
            "xml": xml_data,
            "startlog": startlog_data,
            "ocr": ocr_data,
        },
    }