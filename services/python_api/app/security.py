from __future__ import annotations

import re
from pathlib import PurePath
from typing import Any

from fastapi import HTTPException, UploadFile

from aqis.core.config import get_config


SAFE_FILENAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
SAFE_TEST_NAME_PATTERN = re.compile(r"[^A-Za-z0-9._ -]+")


class RateLimitPlaceholder:
    """Placeholder for future token-bucket or distributed rate limiting."""

    def allow(self, identifier: str) -> bool:
        # TODO: replace with real rate limiting backed by Redis or API gateway policy.
        return True


def sanitize_test_name(value: str | None) -> str | None:
    if value is None:
        return None
    sanitized = SAFE_TEST_NAME_PATTERN.sub("_", value).strip()
    return sanitized or None


def sanitize_upload_filename(value: str | None) -> str:
    raw_value = str(value or "").strip().replace("\\", "/")
    if not raw_value:
        raise HTTPException(status_code=400, detail="Invalid filename: unknown")

    parts = [part for part in PurePath(raw_value).parts if part not in {"", "."}]
    if not parts or any(part == ".." for part in parts):
        raise HTTPException(status_code=400, detail=f"Invalid filename: {raw_value}")

    filename = parts[-1]
    if not SAFE_FILENAME_PATTERN.match(filename):
        raise HTTPException(status_code=400, detail=f"Invalid filename: {raw_value}")
    return filename


async def validate_upload(
    upload: UploadFile | None,
    *,
    required: bool,
    allowed_mime_types: set[str],
    max_size_bytes: int,
) -> bytes | None:
    if upload is None:
        if required:
            raise HTTPException(status_code=400, detail="Required upload is missing.")
        return None

    sanitize_upload_filename(upload.filename)

    content_type = upload.content_type or ""
    if content_type not in allowed_mime_types:
        raise HTTPException(status_code=400, detail=f"Unsupported content type: {content_type or 'unknown'}")

    data = await upload.read()
    if len(data) > max_size_bytes:
        raise HTTPException(status_code=413, detail="Uploaded file exceeds allowed size limit.")
    return data


def allowed_upload_mime_types() -> set[str]:
    return set(get_config().allowed_upload_mime_types)
