from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from aqis.core.config import get_config
from services.python_api.app.schemas import PredictionWithBundleResponse
from services.python_api.app.services.orchestration import analyze_uploaded_artifacts
from services.python_api.app.security import (
    allowed_upload_mime_types,
    sanitize_test_name,
    sanitize_upload_filename,
    validate_upload,
)

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.post("/predict", response_model=PredictionWithBundleResponse)
async def upload_and_predict(
    log_xml: UploadFile = File(..., alias="logXml"),
    start_log: UploadFile = File(..., alias="startLog"),
    screenshots: list[UploadFile] = File(default=[], alias="screenshot"),
    test_name: str | None = Form(default=None, alias="testName"),
) -> PredictionWithBundleResponse:
    try:
        max_size_bytes = get_config().max_upload_size_bytes
        allowed_types = allowed_upload_mime_types()
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
        unified = await analyze_uploaded_artifacts(
            xml_bytes=await validate_upload(
                log_xml,
                required=True,
                allowed_mime_types=allowed_types,
                max_size_bytes=max_size_bytes,
            ) or b"",
            startlog_bytes=await validate_upload(
                start_log,
                required=True,
                allowed_mime_types=allowed_types,
                max_size_bytes=max_size_bytes,
            ) or b"",
            screenshot_bytes_list=screenshot_bytes_list,
            test_name=sanitize_test_name(test_name),
            filenames={
                "logXml": sanitize_upload_filename(log_xml.filename),
                "startLog": sanitize_upload_filename(start_log.filename),
                "screenshots": [sanitize_upload_filename(screenshot.filename) for screenshot in screenshots if screenshot.filename],
            },
        )
        prediction = dict(unified["prediction"])
        prediction["ingestedArtifacts"] = unified["testSummary"]["uploadedArtifacts"]
        prediction["bundle"] = unified["bundle"]
        return prediction
    except HTTPException:
        raise
    except Exception as exc:
        detail = str(exc) or exc.__class__.__name__
        raise HTTPException(status_code=500, detail=detail) from exc
