from typing import Any

from aqis.agents.base_agent import BaseAgent


class ExampleAgent(BaseAgent):
    agent_name = "example"

    def run(self, bundle: dict[str, Any], previous_output: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.reasoning_context(bundle, previous_output)


def test_base_agent_builds_structured_reasoning_context():
    bundle = {
        "testName": "checkout",
        "steps": [
            {"stepName": "open", "errorMessage": ""},
            {"stepName": "submit", "errorMessage": "NoSuchElementException"},
        ],
        "exception": ["TimeoutException", "TimeoutException"],
        "ocrText": "Checkout Submit",
    }

    result = ExampleAgent().run(bundle, {"prior": True})

    assert result["agent"] == "example"
    assert result["failedSteps"] == ["submit"]
    assert result["exceptions"] == ["TimeoutException"]
    assert result["previousOutputKeys"] == ["prior"]
