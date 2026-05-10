from __future__ import annotations

from typing import Any

from aqis.agents.failure_agent import FailureAnalyzerAgent
from aqis.agents.fix_agent import FixSuggestionAgent
from aqis.agents.reporter_agent import ReportAgent
from aqis.agents.retriever_agent import ContextRetrieverAgent
from aqis.agents.test_reader_agent import TestReaderAgent
from aqis.agents.validator_agent import ValidationAgent


def run_agents(bundle: dict[str, Any]) -> dict[str, Any]:
    """Execute the full deterministic multi-agent RCA pipeline."""
    reader = TestReaderAgent()
    failure_analyzer = FailureAnalyzerAgent()
    retriever = ContextRetrieverAgent()
    fixer = FixSuggestionAgent()
    validator = ValidationAgent()
    reporter = ReportAgent()

    reader_output = reader.run(bundle)
    failure_output = failure_analyzer.run(bundle, reader_output)
    retriever_output = retriever.run(bundle, failure_output)
    fix_output = fixer.run(bundle, failure_output)
    validation_output = validator.run(bundle, fix_output)

    aggregate = {
        "test_reader": reader_output,
        "failure_analyzer": failure_output,
        "context_retriever": retriever_output,
        "fix_suggestion": fix_output,
        "validation": validation_output,
    }
    report_output = reporter.run(bundle, aggregate)

    return {
        "testName": bundle.get("testName", ""),
        "agents": {
            "testReader": reader_output,
            "failureAnalyzer": failure_output,
            "contextRetriever": retriever_output,
            "fixSuggestion": fix_output,
            "validation": validation_output,
            "report": report_output,
        },
        "finalReport": report_output,
    }
