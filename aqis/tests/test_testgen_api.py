import asyncio

from aqis.agents.orchestrator import run_agents
from aqis.autofix.orchestrator import generate_autofix
from services.python_api.app.routes.testcases import generate


def test_testcase_generation_route_returns_templates():
    bundle = {
        "testName": "login_test",
        "steps": [
            {
                "stepName": "Enter Username",
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
        "ocrText": "Login\nUsername\nPassword\nGo",
        "raw": {"startlog": {"screenMismatch": False, "exceptions": []}},
    }
    risk_report = {
        "riskScore": 0.75,
        "riskLevel": "HIGH",
        "prediction": "FAIL",
        "reasons": ["locator drift"],
    }
    agent_output = run_agents(bundle)
    autofix_output = generate_autofix(bundle, agent_output)

    payload = asyncio.run(
        generate(
            {
                "bundle": bundle,
                "risk_report": risk_report,
                "agent_output": agent_output,
                "autofix_output": autofix_output,
            }
        )
    )

    assert payload["generatedTests"]
    assert "automationTemplates" in payload
    assert "Selenium" in payload["automationTemplates"]["automationTemplates"]
