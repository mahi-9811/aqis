import asyncio

from services.python_api.app.routes.analyze import analyze_agents


def test_analyze_agents_endpoint():
    payload = asyncio.run(
        analyze_agents(
            {
            "testName": "login_test",
            "steps": [
                {
                    "stepName": "Open Login",
                    "executedProperty": "id=username",
                    "timing": "100",
                    "labels": ["Username"],
                    "errorMessage": "NoSuchElementException",
                }
            ],
            "exception": ["No such element"],
            "retries": 1,
            "autoHeal": [],
            "driftSignals": [],
            "ocrText": "Login Username Password",
            "raw": {"startlog": {"screenMismatch": False, "exceptions": []}},
            }
        )
    )

    assert payload["testName"] == "login_test"
    assert "finalReport" in payload
    assert payload["agents"]["report"]["recommendedFix"]
