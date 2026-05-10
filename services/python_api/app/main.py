from __future__ import annotations

import importlib.util
import json
import time
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from aqis.core.config import get_config
from aqis.core.logger import (
    clear_request_context,
    log_timing,
    set_request_context,
    setup_logger,
    setup_logging,
)
from services.python_api.app.routes import analyze, autofix, learning, predict, testcases
from services.python_api.app.security import RateLimitPlaceholder

setup_logging()
logger = setup_logger("aqis.api")
config = get_config()

app = FastAPI(title="AQIS Python API")
artifact_upload_enabled = importlib.util.find_spec("multipart") is not None
app.state.started_at = time.perf_counter()
app.state.request_count = 0
app.state.error_count = 0
app.state.total_duration_ms = 0.0
app.state.rate_limiter = RateLimitPlaceholder()

if artifact_upload_enabled:
    from services.python_api.app.routes import artifacts

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ui_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    tokens = set_request_context(request_id, request.url.path)
    request.state.request_id = request_id
    request.state.started_at = time.perf_counter()
    app.state.request_count += 1

    if not app.state.rate_limiter.allow(request.client.host if request.client else "unknown"):
        app.state.error_count += 1
        clear_request_context(tokens)
        return JSONResponse(
            status_code=429,
            content={"error": True, "message": "Rate limit exceeded.", "details": "Try again later."},
            headers={"X-Request-ID": request_id},
        )

    try:
        response = await call_next(request)
    except Exception:
        app.state.error_count += 1
        clear_request_context(tokens)
        raise

    elapsed_ms = round((time.perf_counter() - request.state.started_at) * 1000, 2)
    app.state.total_duration_ms += elapsed_ms
    response.headers["X-Request-ID"] = request_id
    if "server" in response.headers:
        del response.headers["server"]
    log_timing(logger, f"{request.method} {request.url.path} -> {response.status_code}", request.state.started_at)
    clear_request_context(tokens)
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    app.state.error_count += 1
    logger.error("http_error status=%s detail=%s", exc.status_code, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "message": str(exc.detail), "details": "HTTP request failed."},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    app.state.error_count += 1
    logger.error("validation_error errors=%s", exc.errors())
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "Request validation failed.",
            "details": json.dumps(exc.errors(), ensure_ascii=False),
        },
    )


@app.exception_handler(json.JSONDecodeError)
async def json_exception_handler(_: Request, exc: json.JSONDecodeError) -> JSONResponse:
    app.state.error_count += 1
    logger.error("json_decode_error detail=%s", str(exc))
    return JSONResponse(
        status_code=400,
        content={"error": True, "message": "Invalid JSON payload.", "details": str(exc)},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    app.state.error_count += 1
    logger.exception("unhandled_exception")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "AQIS encountered an unexpected internal error.",
            "details": str(exc),
        },
    )


@app.get("/health")
async def health() -> dict[str, Any]:
    uptime_seconds = round(time.perf_counter() - app.state.started_at, 2)
    return {"status": "ok", "uptime": uptime_seconds, "artifactUploadEnabled": artifact_upload_enabled}


@app.get("/health/live")
async def health_live() -> dict[str, Any]:
    return {"status": "ok"}


@app.get("/health/ready")
async def health_ready() -> dict[str, Any]:
    return {"status": "ok", "env": config.env}


@app.get("/metrics")
async def metrics() -> PlainTextResponse:
    average_duration = app.state.total_duration_ms / app.state.request_count if app.state.request_count else 0.0
    content = "\n".join(
        [
            f"aqis_requests_total {app.state.request_count}",
            f"aqis_request_errors_total {app.state.error_count}",
            f"aqis_request_duration_avg_ms {average_duration:.2f}",
        ]
    )
    return PlainTextResponse(content)


app.include_router(predict.router)
app.include_router(analyze.router)
app.include_router(autofix.router)
app.include_router(learning.router)
app.include_router(testcases.router)
if artifact_upload_enabled:
    app.include_router(artifacts.router)
