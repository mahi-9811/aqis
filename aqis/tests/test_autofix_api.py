import asyncio

from aqis.agents.orchestrator import run_agents
from services.python_api.app.routes.autofix import autofix


def test_autofix_route_returns_patch():
    bundle = {
        "testName": "login_test",
        "steps": [
            {
                "stepName": "Open Login",
                "executedProperty": "xpath=//input[@id='username']",
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

    agent_output = run_agents(bundle)
    payload = asyncio.run(autofix({"bundle": bundle, "agent_output": agent_output}))

    assert "patch" in payload
    assert "fixes" in payload
    assert payload["confidence"] >= 0.0
