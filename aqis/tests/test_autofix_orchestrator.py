from aqis.agents.orchestrator import run_agents
from aqis.autofix.orchestrator import generate_autofix


def test_generate_autofix_returns_patch_and_confidence():
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
        "ocrText": "Manage Sales Quotations\nSales Quotation",
        "raw": {
            "startlog": {
                "screenMismatch": True,
                "scanFailure": True,
                "exceptions": ["sap.ui TimeoutException"],
            }
        },
    }

    agent_output = run_agents(bundle)
    result = generate_autofix(bundle, agent_output)

    assert result["recommended"] is True
    assert result["confidence"] > 0.0
    assert "+++ AFTER" in result["patch"]
    assert any(fix["fixType"] == "locator" for fix in result["fixes"])
    assert all(fix["rollbackSafe"] is True for fix in result["fixes"])
