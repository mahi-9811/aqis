# python
from typing import Dict, List, Any
from pathlib import Path
from datetime import datetime, timezone
import json
from aqis.core.config import get_config

HISTORY_ROOT = get_config().history_storage_dir


class RunHistoryManager:
    """
    Store and load historical runs for a specific test case.

    Files are saved as:
        data/history/<test_name>/run_<timestamp>.json
    """

    def __init__(self, root: Path = HISTORY_ROOT) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _safe_test_dir(self, test_name: str) -> Path:
        safe = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in test_name)
        path = self.root / safe
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_run(self, bundle: Dict[str, Any], test_name: str) -> Path:
        """
        Persist a run bundle to disk. Returns saved file path.
        """
        test_dir = self._safe_test_dir(test_name)
        # Include microseconds so multiple saves in the same second do not collide.
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        filename = f"run_{ts}.json"
        path = test_dir / filename
        try:
            with path.open("w", encoding="utf-8") as f:
                json.dump(bundle, f, ensure_ascii=False, default=str)
        except Exception as e:
            # bubble up or log in production; keep simple here
            raise e
        return path

    def load_runs(self, test_name: str) -> List[Dict[str, Any]]:
        """
        Load all runs for test_name, sorted oldest -> newest.
        Missing folder -> return empty list.
        """
        test_dir = self._safe_test_dir(test_name)
        runs: List[Dict[str, Any]] = []
        try:
            files = sorted(test_dir.glob("run_*.json"))
            for f in files:
                try:
                    with f.open("r", encoding="utf-8") as fh:
                        runs.append(json.load(fh))
                except Exception:
                    # skip corrupt files
                    continue
        except Exception:
            return []
        return runs
