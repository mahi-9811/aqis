from __future__ import annotations

import importlib.util
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from aqis.agents.orchestrator import run_agents
from aqis.core.config import get_config
from services.python_api.app.schemas import AgentAnalysisResponse, BundlePayload, UnifiedAnalysisResponse
from services.python_api.app.services.orchestration import analyze_bundle, analyze_uploaded_artifacts
from services.python_api.app.security import (
    allowed_upload_mime_types,
    sanitize_test_name,
    sanitize_upload_filename,
    validate_upload,
)

router = APIRouter(prefix="/analyze", tags=["analyze"])
analyze_upload_enabled = importlib.util.find_spec("multipart") is not None


def _bundle_payload_as_dict(bundle: BundlePayload | dict[str, object]) -> dict[str, object]:
    if isinstance(bundle, BundlePayload):
        return bundle.model_dump()
    return bundle


@router.post("/bundle", response_model=UnifiedAnalysisResponse)
async def analyze_bundle_only(bundle: BundlePayload | dict[str, object]) -> UnifiedAnalysisResponse:
    try:
        return analyze_bundle(_bundle_payload_as_dict(bundle))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/agents", response_model=AgentAnalysisResponse)
async def analyze_agents(bundle: BundlePayload | dict[str, object]) -> AgentAnalysisResponse:
    try:
        return run_agents(_bundle_payload_as_dict(bundle))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


if analyze_upload_enabled:
    @router.post("", response_model=UnifiedAnalysisResponse)
    async def analyze(
        log_xml: UploadFile = File(..., alias="logXml"),
        start_log: UploadFile = File(..., alias="startLog"),
        screenshots: list[UploadFile] = File(default=[], alias="screenshot"),
        test_name: str | None = Form(default=None, alias="testName"),
    ) -> UnifiedAnalysisResponse:
        try:
            max_size_bytes = get_config().max_upload_size_bytes
            allowed_types = allowed_upload_mime_types()
            xml_bytes = await validate_upload(
                log_xml,
                required=True,
                allowed_mime_types=allowed_types,
                max_size_bytes=max_size_bytes,
            )
            startlog_bytes = await validate_upload(
                start_log,
                required=True,
                allowed_mime_types=allowed_types,
                max_size_bytes=max_size_bytes,
            )
            screenshot_bytes_list = []
            for screenshot in screenshots:
                screenshot_bytes = await validate_upload(
                    screenshot,
                    required=False,
                    allowed_mime_types=allowed_types,
                    max_size_bytes=max_size_bytes,
                )
                if screenshot_bytes is not None:
                    screenshot_bytes_list.append(screenshot_bytes)
            return await analyze_uploaded_artifacts(
                xml_bytes=xml_bytes or b"",
                startlog_bytes=startlog_bytes or b"",
                screenshot_bytes_list=screenshot_bytes_list,
                test_name=sanitize_test_name(test_name),
                filenames={
                    "logXml": sanitize_upload_filename(log_xml.filename),
                    "startLog": sanitize_upload_filename(start_log.filename),
                    "screenshots": [sanitize_upload_filename(screenshot.filename) for screenshot in screenshots if screenshot.filename],
                },
            )
        except HTTPException:
            raise
        except Exception as exc:
            detail = str(exc) or exc.__class__.__name__
            raise HTTPException(status_code=400, detail=detail) from exc
