# python
from typing import Dict, Any
import re


def _safe_float(v: Any) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0


def _flatten_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return " ".join(_flatten_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_flatten_text(item) for item in value)
    return str(value)


def extract_features(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a failure_bundle into numeric/boolean features.

    Expected keys in bundle:
      - retries (int)
      - autoHeal (list|dict|str)
      - steps -> list of { timing, errorMessage, stepName }
      - raw.startlog -> dict with screenMismatch, scanFailure, exceptions
      - driftSignals -> list/dict
      - exception -> list/str
      - ocrText -> str

    Returns a normalized feature dict.
    """
    features: Dict[str, Any] = {}

    # retries
    features["retries"] = int(bundle.get("retries") or 0)

    # autoheal failures: try to count occurrences
    autoheal = bundle.get("autoHeal", {})
    if isinstance(autoheal, dict):
        autoheal_failures = sum(1 for v in autoheal.values() if v)
    elif isinstance(autoheal, list):
        autoheal_failures = len(autoheal)
    elif isinstance(autoheal, str):
        autoheal_failures = 1 if autoheal else 0
    else:
        autoheal_failures = 0
    features["autoheal_failures"] = int(autoheal_failures)

    # steps: durations and missing elements
    steps = bundle.get("steps") or []
    timings = []
    missing_elements = 0
    locator_mismatch_count = 0
    element_comparison_diffs = 0
    for s in steps:
        t = s.get("timing") or s.get("Timing") or None
        if t is not None:
            try:
                timings.append(float(t))
            except Exception:
                # attempt to extract digits
                m = re.search(r"(\d+\.?\d*)", str(t))
                if m:
                    timings.append(float(m.group(1)))
        em = s.get("errorMessage") or ""
        if isinstance(em, str) and re.search(r"(NoSuchElement|ElementNotFound|NoSuchElementException)", em, re.IGNORECASE):
            missing_elements += 1
        step_text = _flatten_text(s)
        if re.search(r"(locator|selector|xpath|css).{0,40}(mismatch|changed|not found|stale)", step_text, re.IGNORECASE):
            locator_mismatch_count += 1
        if re.search(r"(expected|actual|comparison|diff|does not match|mismatch)", step_text, re.IGNORECASE):
            element_comparison_diffs += 1
    features["stepDuration"] = float(sum(timings) / len(timings)) if timings else 0.0
    features["totalExecutionTime"] = float(sum(timings)) if timings else 0.0
    features["missingElements"] = int(missing_elements)
    features["locatorMismatchCount"] = int(locator_mismatch_count)
    features["elementComparisonDiffs"] = int(element_comparison_diffs)

    # startlog signals
    startlog = bundle.get("raw", {}).get("startlog", {}) or {}
    # boolean flags
    features["screenNotReady"] = bool(startlog.get("screenMismatch") or startlog.get("scanFailure"))
    # environment errors: look for common env keywords in exceptions and startlog text
    env_count = 0
    exceptions = []
    if isinstance(bundle.get("exception"), list):
        exceptions = bundle.get("exception")
    elif bundle.get("exception"):
        exceptions = [bundle.get("exception")]
    # also check startlog exceptions field if present
    if isinstance(startlog.get("exceptions"), list):
        exceptions += startlog.get("exceptions")
    elif isinstance(startlog.get("exceptions"), str):
        exceptions.append(startlog.get("exceptions"))

    env_patterns = re.compile(r"(Timeout|Connection refused|Network|SocketException|UnknownHostException)", re.IGNORECASE)
    sap_ui5_pattern = re.compile(r"(SAPUI5|sap.ui)", re.IGNORECASE)
    sap_count = 0
    for ex in exceptions:
        try:
            exs = str(ex)
            if env_patterns.search(exs):
                env_count += 1
            if sap_ui5_pattern.search(exs):
                sap_count += 1
        except Exception:
            continue
    features["environmentErrorCount"] = int(env_count)
    features["sap_ui5_errors"] = int(sap_count)

    # driftScore: simple heuristic from driftSignals and missingElements
    drift_signals = bundle.get("driftSignals") or {}
    drift_count = 0
    if isinstance(drift_signals, dict):
        drift_count = sum(1 for v in drift_signals.values() if v)
    elif isinstance(drift_signals, list):
        drift_count = len(drift_signals)
    drift_text = _flatten_text(drift_signals)
    if re.search(r"(locator|selector|xpath|css)", drift_text, re.IGNORECASE):
        features["locatorMismatchCount"] += 1
    if re.search(r"(expected|actual|comparison|diff|layout)", drift_text, re.IGNORECASE):
        features["elementComparisonDiffs"] += 1
    features["driftScore"] = float(
        drift_count
        + features["missingElements"]
        + features["locatorMismatchCount"] * 0.75
        + features["elementComparisonDiffs"] * 0.5
    )

    # ui error trend placeholder: attempt to detect repeated UI errors from ocrText / exception
    ocr = str(bundle.get("ocrText") or bundle.get("raw", {}).get("ocr", "") or "")
    ui_error_signals = 0
    if "not able to scan the page" in ocr.lower():
        ui_error_signals += 1
    if re.search(r"(overlap|truncated|misaligned|not visible|blank|modal|toast|busy indicator)", ocr, re.IGNORECASE):
        ui_error_signals += 1
    features["uiErrorSignals"] = int(ui_error_signals)
    visible_lines = [line.strip() for line in ocr.splitlines() if line.strip()]
    duplicate_lines = len(visible_lines) - len(set(visible_lines))
    layout_keywords = len(re.findall(r"(button|input|field|dialog|table|column|row|label)", ocr, re.IGNORECASE))
    features["ocrLayoutDiffs"] = int(duplicate_lines + min(5, layout_keywords // 4))

    # combined instability signals
    features["instabilityIndex"] = (
        features["driftScore"] * 0.5
        + features["autoheal_failures"] * 0.3
        + features["environmentErrorCount"] * 0.2
        + features["locatorMismatchCount"] * 0.2
        + features["ocrLayoutDiffs"] * 0.1
    )

    # normalize numeric types
    for k, v in list(features.items()):
        if isinstance(v, bool):
            features[k] = int(v)
        elif v is None:
            features[k] = 0.0

    return features
