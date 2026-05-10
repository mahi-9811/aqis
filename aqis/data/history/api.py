from typing import Dict, Any, Optional
from .storage_adapter import StorageAdapter
from .event_logger import append_event
from .engine import calculateTrends, compareCurrentVsPrevious

storage = StorageAdapter()

def summarize_bundle(bundle: Dict[str,Any]) -> Dict[str,Any]:
    """
    Convert Phase1 failure_bundle into compact metadata for history.
    """
    steps = bundle.get("steps", [])
    avg_timing = None
    try:
        timings = [float(s.get("timing")) for s in steps if s.get("timing") is not None]
        avg_timing = sum(timings)/len(timings) if timings else None
    except Exception:
        avg_timing = None

    return {
        "test_name": bundle.get("testName",""),
        "failed": bool(bundle.get("exception") or (bundle.get("steps") and any(s.get("errorMessage") for s in bundle.get("steps",[])))),
        "retries": int(bundle.get("retries",0)),
        "exception": (bundle.get("exception") or [""])[0] if isinstance(bundle.get("exception"), list) else bundle.get("exception",""),
        "avg_timing_ms": avg_timing,
        "drift": bool(bundle.get("driftSignals")),
        "version": 1
    }

def addHistoryRecord(failure_bundle: Dict[str,Any]) -> str:
    summary = summarize_bundle(failure_bundle)
    record_id = storage.insert_record(summary, failure_bundle)
    append_event("history.add", {"id":record_id, "test_name": summary["test_name"]})
    return record_id

def getHistory(test_name: str, limit: int = 100, since: Optional[str]=None):
    return storage.query_history(test_name, limit=limit, since=since)

def calculateTrendsAPI(test_name: str, metric: str = "failure_rate", window: Optional[str]=None):
    records = storage.query_history(test_name, limit=50)  # choose limit heuristically
    trend = calculateTrends(records, metric)
    append_event("trend.calculate", {"test_name": test_name, "metric": metric, "trend": trend["trend"]})
    return trend