import asyncio

from aqis.risk_engine.history_manager import RunHistoryManager
from services.python_api.app.routes.analyze import analyze_bundle_only
from services.python_api.app.services import orchestration


def test_analyze_bundle_returns_unified_response(tmp_path):
    bundle = {
        "testName": "sales_quote_search",
        "steps": [
            {
                "stepName": "Enter Sales Quotation value",
                "executedProperty": "xpath=//input[@id='C_QuotationWl_F1852--filterItemControl']",
                "timing": "240",
                "labels": ["Sales Quotation"],
                "errorMessage": "NoSuchElementException",
            }
        ],
        "exception": ["Exception: No such element found"],
        "retries": 2,
        "autoHeal": ["failed"],
        "driftSignals": ["locator_mismatch"],
        "ocrText": "Manage Sales Quotations\nSales Quotation\nGo",
        "raw": {
            "startlog": {
                "screenMismatch": True,
                "scanFailure": True,
                "exceptions": ["sap.ui TimeoutException"],
            }
        },
    }

    prior_bundle = {
        **bundle,
        "steps": [
            {
                "stepName": "Enter Sales Quotation value",
                "executedProperty": "xpath=//input[@id='C_QuotationWl_F1852--filterItemControl']",
                "timing": "200",
                "labels": ["Sales Quotation"],
                "errorMessage": "",
            }
        ],
        "exception": [],
        "retries": 0,
    }

    manager = RunHistoryManager(root=tmp_path / "history")
    manager.save_run(prior_bundle, "sales_quote_search")
    original = orchestration.history_manager
    orchestration.history_manager = manager
    try:
        response = orchestration.analyze_bundle(bundle, {"logXml": "log.xml", "startLog": "STARTLog.txt"})
    finally:
        orchestration.history_manager = original

    assert set(response.keys()) >= {
        "testSummary",
        "prediction",
        "rootCauseAnalysis",
        "autoFix",
        "generatedTestCases",
        "trendSummary",
        "nextRunRecommendation",
    }
    assert response["prediction"]["available"] is True
    assert "Prediction unavailable" not in response["prediction"]["message"]
    assert "priorKnowledge" in response["rootCauseAnalysis"]
    assert "Screenshot not provided" in response["warnings"][0]


def test_analyze_bundle_handles_insufficient_history(tmp_path):
    bundle = {
        "testName": "single_run_case",
        "steps": [{"stepName": "Open", "timing": "50", "labels": ["Open"], "errorMessage": ""}],
        "exception": [],
        "retries": 0,
        "autoHeal": [],
        "driftSignals": [],
        "ocrText": "",
        "raw": {"startlog": {"screenMismatch": False, "exceptions": []}},
    }

    manager = RunHistoryManager(root=tmp_path / "history")
    original = orchestration.history_manager
    orchestration.history_manager = manager
    try:
        response = asyncio.run(analyze_bundle_only(bundle))
    finally:
        orchestration.history_manager = original

    assert response["prediction"]["available"] is False
    assert response["prediction"]["message"] == "Prediction unavailable — insufficient run history."
    assert "Prediction unavailable — insufficient run history." in response["warnings"]


def test_parse_uploaded_artifacts_rejects_corrupt_xml():
    try:
        asyncio.run(
            orchestration.parse_uploaded_artifacts(
                xml_bytes=b"<root",
                startlog_bytes=b"",
                screenshot_bytes_list=None,
                test_name="broken_case",
                filenames={"logXml": "log.xml", "startLog": "STARTLog.txt", "screenshots": []},
            )
        )
    except ValueError as exc:
        assert "Corrupt log.xml" in str(exc)
    else:
        raise AssertionError("Expected corrupt XML to raise ValueError")
