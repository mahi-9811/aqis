from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from aqis.autofix.orchestrator import generate_autofix
from services.python_api.app.schemas import AutofixResponse

router = APIRouter(tags=["autofix"])


@router.post("/autofix", response_model=AutofixResponse)
async def autofix(payload: dict[str, Any]) -> AutofixResponse:
    try:
        bundle = payload.get("bundle")
        agent_output = payload.get("agent_output")
        if not isinstance(bundle, dict):
            raise ValueError("bundle must be provided")
        if not isinstance(agent_output, dict):
            raise ValueError("agent_output must be provided")
        return generate_autofix(bundle, agent_output)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
