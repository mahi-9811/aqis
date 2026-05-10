from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT_DIR / "config"


@dataclass(frozen=True)
class AppConfig:
    env: str
    api_base_url: str
    log_level: str
    ui_origins: list[str]
    history_storage_dir: Path
    vector_store_path: Path
    learning_storage_dir: Path
    screenshot_storage_dir: Path
    max_upload_size_bytes: int
    allowed_upload_mime_types: list[str]
    request_timeout_seconds: float
    enable_json_logs: bool
    healthcheck_sample_test: str


def _load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _env_name() -> str:
    return str(os.getenv("ENV", "DEV")).upper()


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    env = _env_name()
    env_file = CONFIG_DIR / f"{env.lower()}.env"
    file_values = _load_env_file(env_file)

    def read(key: str, default: str) -> str:
        return os.getenv(key, file_values.get(key, default))

    def read_list(key: str, default: str) -> list[str]:
        return [item.strip() for item in read(key, default).split(",") if item.strip()]

    return AppConfig(
        env=env,
        api_base_url=read("API_BASE_URL", "http://localhost:8000"),
        log_level=read("LOG_LEVEL", "INFO").upper(),
        ui_origins=read_list("UI_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:8080"),
        history_storage_dir=(ROOT_DIR / read("HISTORY_STORAGE_DIR", "data/history")).resolve(),
        vector_store_path=(ROOT_DIR / read("VECTOR_STORE_PATH", "data/learning/vector_store.json")).resolve(),
        learning_storage_dir=(ROOT_DIR / read("LEARNING_STORAGE_DIR", "data/learning")).resolve(),
        screenshot_storage_dir=(ROOT_DIR / read("SCREENSHOT_STORAGE_DIR", "data/screenshots")).resolve(),
        max_upload_size_bytes=int(read("MAX_UPLOAD_SIZE_BYTES", str(10 * 1024 * 1024))),
        allowed_upload_mime_types=read_list(
            "ALLOWED_UPLOAD_MIME_TYPES",
            "text/xml,application/xml,text/plain,image/png,image/jpeg,image/jpg",
        ),
        request_timeout_seconds=float(read("REQUEST_TIMEOUT_SECONDS", "5.0")),
        enable_json_logs=read("ENABLE_JSON_LOGS", "true").lower() == "true",
        healthcheck_sample_test=read("HEALTHCHECK_SAMPLE_TEST", "testsample"),
    )
