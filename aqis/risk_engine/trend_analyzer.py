# python
from typing import Dict, List, Any
from statistics import mean
import math


def _slope(values: List[float]) -> float:
    """
    Simple least-squares slope for equally spaced samples.
    Returns slope per step index.
    """
    n = len(values)
    if n < 2:
        return 0.0
    xs = list(range(n))
    x_mean = mean(xs)
    y_mean = mean(values)
    num = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, values))
    den = sum((x - x_mean) ** 2 for x in xs) or 1.0
    return num / den


def analyze_trends(features_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Given a list of feature dicts (oldest -> newest), compute trend signals.
    """
    result: Dict[str, Any] = {
        "timingSlope": 0.0,
        "retryTrend": "stable",
        "driftTrend": "stable",
        "uiErrorSpike": False,
        "autoHealDeterioration": False,
    }

    if not features_list:
        return result

    # Extract series
    step_durations = [float(f.get("stepDuration", 0.0)) for f in features_list]
    retries = [int(f.get("retries", 0)) for f in features_list]
    drifts = [float(f.get("driftScore", 0.0)) for f in features_list]
    ui_signals = [int(f.get("uiErrorSignals", 0)) for f in features_list]
    autoheal = [int(f.get("autoheal_failures", 0)) for f in features_list]

    # timing slope
    result["timingSlope"] = float(_slope(step_durations))

    # retry trend: compare last 3 avg vs previous 3 avg
    def _trend_label(series: List[float]) -> str:
        if len(series) < 3:
            if len(series) == 1:
                return "stable"
            return "stable"
        last = mean(series[-3:])
        prev = mean(series[:-3]) if len(series) > 3 else mean(series[:-3]) if series[:-3] else mean(series[:len(series)-1])
        # fallback if prev is zero-length
        if math.isclose(prev, 0.0, abs_tol=1e-9):
            if last > 0:
                return "rising"
            return "stable"
        if last > prev * 1.1:
            return "rising"
        if last < prev * 0.9:
            return "falling"
        return "stable"

    result["retryTrend"] = _trend_label(retries)

    # drift trend: evaluate average drift increase
    if len(drifts) < 2:
        result["driftTrend"] = "stable"
    else:
        slope_drift = _slope(drifts)
        if slope_drift > 0.01:
            result["driftTrend"] = "increasing"
        elif slope_drift < -0.01:
            result["driftTrend"] = "decreasing"
        else:
            # intermittent if variance is high but slope small
            variance = (sum((d - mean(drifts)) ** 2 for d in drifts) / max(1, len(drifts) - 1))
            result["driftTrend"] = "intermittent" if variance > 1.0 else "stable"

    # ui error spike detection: last > mean(prev)*2 OR absolute jump
    if len(ui_signals) >= 2:
        prev_mean = mean(ui_signals[:-1]) if len(ui_signals) > 1 else 0.0
        last = ui_signals[-1]
        if prev_mean > 0 and last > prev_mean * 2:
            result["uiErrorSpike"] = True
        elif last - prev_mean >= 3:
            result["uiErrorSpike"] = True

    # autoHeal deterioration: rising autoheal failures trend
    if len(autoheal) >= 2:
        if _slope(autoheal) > 0.05:
            result["autoHealDeterioration"] = True

    # TODO: add seasonality and windowed analysis for robustness

    return result