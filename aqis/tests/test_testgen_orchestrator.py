from aqis.agents.orchestrator import run_agents
from aqis.autofix.orchestrator import generate_autofix
from aqis.risk_engine.prediction_engine import predict_next_run
from aqis.risk_engine.history_manager import RunHistoryManager
from aqis.testgen.orchestrator import generate_test_cases


def test_generate_test_cases_returns_ranked_output(tmp_path):
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
        "ocrText": "Manage Sales Quotations\nSales Quotation\nSold-to Party\nCustomer Reference\nGo",
        "raw": {
            "startlog": {
                "screenMismatch": True,
                "scanFailure": True,
                "exceptions": ["sap.ui TimeoutException"],
            }
        },
    }

    manager = RunHistoryManager(root=tmp_path / "history")
    manager.save_run(bundle, "sales_quote_search")
    manager.save_run(bundle, "sales_quote_search")

    from aqis.risk_engine import prediction_engine

    original_history = prediction_engine.history
    prediction_engine.history = manager
    try:
        risk_report = predict_next_run("sales_quote_search")
    finally:
        prediction_engine.history = original_history

    agent_output = run_agents(bundle)
    autofix_output = generate_autofix(bundle, agent_output)
    result = generate_test_cases(bundle, risk_report, agent_output, autofix_output)

    assert result["priorityOrder"] == ["HIGH", "MEDIUM", "LOW"]
    assert result["generatedTests"]
    assert result["automationTemplates"]["gherkin"].startswith("Feature:")
    assert result["recommendation"]
    assert "missingFields" in result["coverageAnalysis"]
