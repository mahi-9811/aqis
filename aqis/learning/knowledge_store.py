from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Any
from aqis.core.config import get_config


KNOWLEDGE_ROOT = get_config().learning_storage_dir


class KnowledgeStore:
    """Persist structured run knowledge as JSON records for MVP learning."""

    def __init__(self, root: Path = KNOWLEDGE_ROOT) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def store_run_knowledge(self, run_summary: dict[str, Any]) -> Path:
        test_name = str(run_summary.get("testName") or "").strip()
        if not test_name:
            raise ValueError("run_summary must include testName")

        test_dir = self._safe_test_dir(test_name)
        timestamp = str(run_summary.get("timestamp") or datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ"))
        path = test_dir / f"knowledge_{timestamp}.json"
        with path.open("w", encoding="utf-8") as handle:
            json.dump(run_summary, handle, ensure_ascii=False, indent=2, default=str)
        return path

    def load_knowledge(self, test_name: str) -> list[dict[str, Any]]:
        test_dir = self._safe_test_dir(test_name)
        records: list[dict[str, Any]] = []
        for path in sorted(test_dir.glob("knowledge_*.json")):
            try:
                with path.open("r", encoding="utf-8") as handle:
                    records.append(json.load(handle))
            except Exception:
                continue
        return records

    def load_all_knowledge(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for test_dir in sorted(path for path in self.root.iterdir() if path.is_dir()):
            for path in sorted(test_dir.glob("knowledge_*.json")):
                try:
                    with path.open("r", encoding="utf-8") as handle:
                        records.append(json.load(handle))
                except Exception:
                    continue
        return records

    def stats(self) -> dict[str, Any]:
        records = self.load_all_knowledge()
        successes = sum(1 for record in records if record.get("feedback", {}).get("fixOutcome") == "success")
        failures = sum(1 for record in records if record.get("feedback", {}).get("fixOutcome") == "failure")
        test_names = sorted({str(record.get("testName") or "") for record in records if record.get("testName")})
        return {
            "storedRuns": len(records),
            "knownTests": len(test_names),
            "fixSuccessCount": successes,
            "fixFailureCount": failures,
        }

    def _safe_test_dir(self, test_name: str) -> Path:
        safe = "".join(char if char.isalnum() or char in ("_", "-") else "_" for char in test_name)
        path = self.root / safe
        path.mkdir(parents=True, exist_ok=True)
        return path
