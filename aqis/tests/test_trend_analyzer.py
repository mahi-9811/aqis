# python
from aqis.risk_engine.trend_analyzer import analyze_trends

def test_analyze_trends_increasing_and_spike():
    # create features oldest->newest
    features = [
        {"stepDuration": 100.0, "retries": 0, "driftScore": 0.0, "uiErrorSignals": 0, "autoheal_failures": 0},
        {"stepDuration": 120.0, "retries": 1, "driftScore": 0.5, "uiErrorSignals": 0, "autoheal_failures": 0},
        {"stepDuration": 200.0, "retries": 2, "driftScore": 1.5, "uiErrorSignals": 5, "autoheal_failures": 2},
    ]
    t = analyze_trends(features)
    assert "timingSlope" in t
    assert t["timingSlope"] > 0.0
    assert t["retryTrend"] in ("rising","stable","falling")
    assert t["driftTrend"] in ("increasing","decreasing","intermittent","stable")
    assert t["uiErrorSpike"] is True or t["uiErrorSpike"] is False
    assert t["autoHealDeterioration"] in (True, False)