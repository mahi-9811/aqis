# python
from pathlib import Path
from aqis.risk_engine.history_manager import RunHistoryManager
import json

def test_save_and_load_runs(tmp_path: Path):
    mgr = RunHistoryManager(root=tmp_path / "history_root")
    bundle1 = {"testName": "T1", "steps": [{"stepName": "s1"}], "retries": 0}
    bundle2 = {"testName": "T1", "steps": [{"stepName": "s2"}], "retries": 1}

    p1 = mgr.save_run(bundle1, "T1")
    p2 = mgr.save_run(bundle2, "T1")

    assert p1.exists()
    assert p2.exists()

    runs = mgr.load_runs("T1")
    assert isinstance(runs, list)
    # saved order is oldest -> newest
    assert len(runs) == 2
    assert runs[0]["testName"] == "T1"