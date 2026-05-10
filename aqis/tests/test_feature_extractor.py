# python
from aqis.risk_engine.feature_extractor import extract_features

def test_extract_features_basic():
    bundle = {
        "testName": "LoginTest",
        "retries": 2,
        "steps": [
            {"stepName": "open", "timing": "100"},
            {"stepName": "click", "timing": "200", "errorMessage": "NoSuchElementException"},
        ],
        "driftSignals": ["layout_changed", "locator_mismatch"],
        "exception": ["ElementNotFound"],
        "ocrText": "Page Title: Login",
        "raw": {"startlog": {"screenMismatch": True, "exceptions": ["TimeoutException"]}, "ocr": "Page Title"}
    }
    f = extract_features(bundle)
    assert isinstance(f, dict)
    assert f["retries"] == 2
    assert f["missingElements"] >= 1
    assert f["stepDuration"] > 0.0
    assert f["screenNotReady"] in (0,1)
    assert f["environmentErrorCount"] >= 1
    assert "driftScore" in f
    assert f["locatorMismatchCount"] >= 1
    assert f["elementComparisonDiffs"] >= 1
    assert "ocrLayoutDiffs" in f
