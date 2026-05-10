from aqis.risk_engine.prediction_engine import predict_from_runs


def test_predict_from_runs_returns_calibrated_probabilities():
    runs = [
        {"steps": [{"stepName": "open", "timing": "100"}], "retries": 0},
        {
            "steps": [{"stepName": "submit", "timing": "300", "errorMessage": "NoSuchElementException"}],
            "retries": 2,
            "autoHeal": ["failed"],
            "exception": ["TimeoutException"],
            "driftSignals": ["locator_mismatch"],
        },
    ]

    result = predict_from_runs("checkout", runs)

    assert set(result["probabilities"]) == {"PASS", "FLAKY", "FAIL"}
    assert round(sum(result["probabilities"].values()), 2) == 1.0
    assert result["calibration"]["method"] == "risk_history_blend"
    assert result["confidence"] > 0.0


def test_predict_from_runs_uses_cold_start_prior_without_history():
    result = predict_from_runs("new_test", [])

    assert result["prediction"] == "PASS"
    assert result["probabilities"]["PASS"] > result["probabilities"]["FAIL"]
    assert result["calibration"]["method"] == "cold_start_prior"
