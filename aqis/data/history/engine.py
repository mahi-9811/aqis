from typing import Dict, Any, List
from statistics import mean
from datetime import datetime
import math

# Input: records from StorageAdapter.query_history()
def calculateTrends(records: List[Dict[str,Any]], metric: str = "failure_rate") -> Dict[str,Any]:
    """
    Calculate simple trend for a metric across records.
    metric options: failure_rate, avg_timing_ms, retries
    Returns trend summary with series, trend label, magnitude, confidence.
    """
    # build timeseries (oldest -> newest)
    series = []
    for r in reversed(records):
        ts = r["timestamp"]
        if metric == "failure_rate":
            val = 1.0 if r["failed"] else 0.0
        else:
            val = r.get(metric) if r.get(metric) is not None else 0.0
        series.append({"ts": ts, "value": float(val)})

    if len(series) < 2:
        return {
            "metric": metric, "trend": "no_data", "magnitude": 0.0, "confidence": 0.0, "series": series
        }

    values = [p["value"] for p in series]
    # simple linear trend estimate (slope)
    n = len(values)
    xs = list(range(n))
    x_mean = mean(xs)
    y_mean = mean(values)
    num = sum((x - x_mean)*(y - y_mean) for x,y in zip(xs, values))
    den = sum((x - x_mean)**2 for x in xs) or 1.0
    slope = num / den
    # magnitude normalized by mean
    magnitude = slope / (abs(y_mean) + 1e-6)
    # heuristic confidence based on sample size and variance
    variance = max(1e-6, sum((y - y_mean)**2 for y in values)/(n-1))
    confidence = min(1.0, min(0.99, 1.0/(1.0 + variance))) * (1 - 1/(n+1))

    if abs(magnitude) < 0.02:
        trend = "no_change"
    elif magnitude > 0:
        trend = "increase"
    else:
        trend = "decrease"

    return {
        "metric": metric,
        "trend": trend,
        "magnitude": float(magnitude),
        "confidence": float(confidence),
        "series": series
    }

def compareCurrentVsPrevious(current: Dict[str,Any], previous: Dict[str,Any]) -> Dict[str,Any]:
    """
    Compare two summary records and surface deltas for key metrics.
    """
    deltas = {}
    for k in ("retries","avg_timing_ms"):
        cur = current.get(k)
        prev = previous.get(k)
        if cur is None or prev is None:
            deltas[k] = {"status":"unknown","delta":None}
            continue
        try:
            delta = cur - prev
            pct = (delta / (prev + 1e-6))
            status = "increase" if delta > 0 else ("decrease" if delta < 0 else "no_change")
            deltas[k] = {"status":status,"delta":delta,"pct_change":pct}
        except Exception as e:
            deltas[k] = {"status":"error","error":str(e)}
    # exceptions comparison
    cur_exc = current.get("exception","")
    prev_exc = previous.get("exception","")
    deltas["exception_changed"] = cur_exc != prev_exc
    return deltas