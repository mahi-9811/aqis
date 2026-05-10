from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from aqis.testgen.orchestrator import generate_test_cases
from services.python_api.app.schemas import GeneratedTestCasesResponse

router = APIRouter(prefix="/testcases", tags=["testcases"])


@router.post("/generate", response_model=GeneratedTestCasesResponse)
async def generate(payload: dict[str, Any]) -> GeneratedTestCasesResponse:
    try:
        bundle = payload.get("bundle")
        risk_report = payload.get("risk_report")
        agent_output = payload.get("agent_output")
        autofix_output = payload.get("autofix_output")
        if not isinstance(bundle, dict):
            raise ValueError("bundle must be provided")
        if not isinstance(risk_report, dict):
            raise ValueError("risk_report must be provided")
        if not isinstance(agent_output, dict):
            raise ValueError("agent_output must be provided")
        return generate_test_cases(bundle, risk_report, agent_output, autofix_output)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
