# python
from aqis.risk_engine.risk_scorer import compute_risk_score

def test_compute_risk_score_high():
    features = {
        "driftScore": 4.0,
        "missingElements": 2,
        "environmentErrorCount": 1,
    }
    trends = {
        "retryTrend": "rising",
        "autoHealDeterioration": True,
        "timingSlope": 300.0,
        "uiErrorSpike": True,
    }
    result = compute_risk_score(features, trends)
    assert "riskScore" in result
    assert 0.0 <= result["riskScore"] <= 1.0
    assert result["riskLevel"] in ("HIGH","MEDIUM","LOW")
    assert result["prediction"] in ("FAIL","FLAKY","PASS")
    assert isinstance(result["reasons"], list)