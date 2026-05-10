from aqis.agents.orchestrator import run_agents


def test_run_agents_returns_structured_report():
    bundle = {
        "testName": "sales_quote_search",
        "steps": [
            {
                "stepName": "Open Quotations",
                "executedProperty": "xpath=//div[@id='header']",
                "timing": "120",
                "labels": ["Sales Quotation"],
                "errorMessage": "",
            },
            {
                "stepName": "Enter Sales Quotation value",
                "executedProperty": "xpath=//input[@name='quotation']",
                "timing": "240",
                "labels": ["Sales Quotation"],
                "errorMessage": "NoSuchElementException",
            },
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

    result = run_agents(bundle)

    assert result["testName"] == "sales_quote_search"
    assert result["agents"]["failureAnalyzer"]["failureCategory"] in {
        "LOCATOR_NOT_FOUND",
        "PAGE_LOAD_TIMING",
    }
    assert result["agents"]["validation"]["fixApproved"] is True
    assert result["finalReport"]["recommendedFix"]
    assert result["finalReport"]["riskLevel"] in {"HIGH", "MEDIUM", "LOW"}
