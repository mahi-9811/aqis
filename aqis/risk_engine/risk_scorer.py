# python
from typing import Dict, Any, List


def _flag_score(flag: bool) -> float:
    return 1.0 if flag else 0.0


def _trend_flag(trend: str) -> float:
    return 1.0 if trend in ("rising", "increasing") else 0.5 if trend == "intermittent" else 0.0


def compute_risk_score(features: Dict[str, Any], trends: Dict[str, Any]) -> Dict[str, Any]:
    """
    Combine feature + trend signals into a risk score between 0.0 and 1.0.

    Weights:
      0.20 driftScore
      0.15 retryTrend (direction)
      0.20 retryVolume (absolute retry count)
      0.15 autoHealDeterioration
      0.15 timingSlopeNormalized
      0.15 uiErrorSpike
    """
    reasons: List[str] = []

    drift_score = float(features.get("driftScore", 0.0))
    drift_norm = min(1.0, drift_score / 5.0)

    retry_trend_flag = _trend_flag(trends.get("retryTrend", "stable"))
    if retry_trend_flag > 0:
        reasons.append("retry trend indicates instability")

    # Absolute retry volume: normalize against a cap of 10 retries = full score
    retry_count = float(features.get("retries", 0.0))
    retry_volume = min(1.0, retry_count / 10.0)
    if retry_count >= 5:
        reasons.append(f"high retry count ({int(retry_count)})")

    autoheal_flag = 1.0 if trends.get("autoHealDeterioration", False) else 0.0
    if autoheal_flag:
        reasons.append("auto-heal failures increasing")

    timing_slope = float(trends.get("timingSlope", 0.0))
    timing_norm = min(1.0, abs(timing_slope) / 100.0)

    ui_spike_flag = 1.0 if trends.get("uiErrorSpike", False) else 0.0
    if ui_spike_flag:
        reasons.append("UI error spike detected")

    # build weighted score
    risk = (
        0.20 * drift_norm
        + 0.15 * retry_trend_flag
        + 0.20 * retry_volume
        + 0.15 * autoheal_flag
        + 0.15 * timing_norm
        + 0.15 * ui_spike_flag
    )

    # clamp
    risk = max(0.0, min(1.0, risk))

    # derive level and prediction
    if risk >= 0.7:
        level = "HIGH"
        prediction = "FAIL"
    elif risk >= 0.4:
        level = "MEDIUM"
        prediction = "FLAKY"
    else:
        level = "LOW"
        prediction = "PASS"

    # add reasons from features
    if features.get("missingElements", 0) > 0:
        reasons.append("missing elements detected")
    if features.get("environmentErrorCount", 0) > 0:
        reasons.append("environment errors observed")

    return {
        "riskScore": round(risk, 3),
        "riskLevel": level,
        "prediction": prediction,
        "reasons": reasons,
        "components": {
            "drift_norm": drift_norm,
            "retry_trend_flag": retry_trend_flag,
            "autoheal_flag": autoheal_flag,
            "timing_norm": timing_norm,
            "ui_spike_flag": ui_spike_flag,
        },
    }