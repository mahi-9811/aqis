from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from aqis.core.logger import setup_logger


class BaseAgent(ABC):
    """Shared base for deterministic RCA agents."""

    agent_name: str = "base_agent"

    def __init__(self) -> None:
        self.logger = setup_logger(f"aqis.agents.{self.agent_name}")

    @abstractmethod
    def run(self, bundle: dict[str, Any], previous_output: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Execute the agent on the normalized bundle and previous agent output.
        """

    def validate_bundle(self, bundle: dict[str, Any]) -> None:
        """Guard against malformed bundle inputs before agent logic runs."""
        if not isinstance(bundle, dict):
            raise TypeError("bundle must be a dictionary")

        if not bundle.get("testName"):
            raise ValueError("bundle must include testName")

        steps = bundle.get("steps")
        if steps is not None and not isinstance(steps, list):
            raise ValueError("bundle steps must be a list when present")

    def log_start(self, bundle: dict[str, Any]) -> None:
        self.logger.info("running agent=%s test=%s", self.agent_name, bundle.get("testName", ""))

    def log_end(self, result: dict[str, Any]) -> None:
        self.logger.info("completed agent=%s keys=%s", self.agent_name, sorted(result.keys()))

    def safe_text(self, value: Any) -> str:
        return str(value or "").strip()

    def listify(self, value: Any) -> list[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    def unique_ordered(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for value in values:
            if value and value not in seen:
                seen.add(value)
                ordered.append(value)
        return ordered

    def reasoning_context(
        self,
        bundle: dict[str, Any],
        previous_output: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build a compact, structured context block for deterministic agent decisions."""
        self.validate_bundle(bundle)
        steps = bundle.get("steps") or []
        exceptions = [self.safe_text(item) for item in self.listify(bundle.get("exception"))]
        error_messages = [
            self.safe_text(step.get("errorMessage"))
            for step in steps
            if isinstance(step, dict) and self.safe_text(step.get("errorMessage"))
        ]
        return {
            "agent": self.agent_name,
            "testName": self.safe_text(bundle.get("testName")),
            "stepCount": len(steps),
            "failedSteps": [
                self.safe_text(step.get("stepName") or "Unknown step")
                for step in steps
                if isinstance(step, dict) and self.safe_text(step.get("errorMessage"))
            ],
            "errorMessages": self.unique_ordered(error_messages),
            "exceptions": self.unique_ordered(exceptions),
            "ocrPreview": self.safe_text(bundle.get("ocrText"))[:300],
            "previousOutputKeys": sorted((previous_output or {}).keys()),
        }
