from typing import Any, Dict
import re


def parse_startlog(text: str) -> Dict[str, Any]:
    """
    Parse STARTLog.txt and extract retries, exceptions, and signals.

    Args:
        text (str): The content of the STARTLog.txt file.

    Returns:
        dict: Extracted data including retries, exceptions, and signals.
    """
    retries = len(re.findall(r"Retrying", text))
    exceptions = re.findall(r"Exception: (.+)", text)
    auto_heal_signals = re.findall(r"AutoHeal: (.+)", text)
    drift_signals = re.findall(r"DriftSignal: (.+)", text)
    screen_mismatch = "Current screen is not appropriate" in text
    scan_failure = "not able to scan the page" in text

    return {
        "retries": retries,
        "exceptions": exceptions,
        "autoHeal": auto_heal_signals,
        "driftSignals": drift_signals,
        "screenMismatch": screen_mismatch,
        "scanFailure": scan_failure,
    }