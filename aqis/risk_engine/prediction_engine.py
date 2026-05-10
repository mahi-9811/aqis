# python
from typing import Dict, Any, List
from .history_manager import RunHistoryManager
from .feature_extractor import extract_features
from .trend_analyzer import analyze_trends
from .risk_scorer import compute_risk_score

history = RunHistoryManager()


def _summarize_run(run: Dict[str, Any], run_number: int) -> Dict[str, Any]:
    steps = run.get("steps") or []
    latest_step = steps[-1] if steps else {}
    exception_count = len(run.get("exception") or [])
    retries = int(run.get("retries") or 0)
    autoheal_count = len(run.get("autoHeal") or [])
    error_message = str(latest_step.get("errorMessage") or "").strip()

    status = "PASS"
    if retries > 1 or autoheal_count > 0:
        status = "FLAKY"
    if error_message or exception_count > 0:
        status = "FAIL"

    return {
        "runNumber": run_number,
        "stepName": latest_step.get("stepName") or "Unknown step",
        "status": status,
        "retries": retries,
        "exceptionCount": exception_count,
        "autoHealCount": autoheal_count,
        "errorMessage": error_message,
    }


def _historical_outcome_rates(runs: List[Dict[str, Any]]) -> Dict[str, float]:
    if not runs:
        return {"passRate": 0.0, "flakyRate": 0.0, "failRate": 0.0}

    counts = {"PASS": 0, "FLAKY": 0, "FAIL": 0}
    for index, run in enumerate(runs):
        status = _summarize_run(run, index + 1)["status"]
        counts[status] += 1

    total = float(len(runs))
    return {
        "passRate": round(counts["PASS"] / total, 3),
        "flakyRate": round(counts["FLAKY"] / total, 3),
        "failRate": round(counts["FAIL"] / total, 3),
    }


def _calibrated_probabilities(risk_score: float, runs: List[Dict[str, Any]]) -> Dict[str, float]:
    historical = _historical_outcome_rates(runs)
    base_fail = min(0.95, max(0.03, risk_score))
    base_flaky = min(0.7, max(0.05, 1.0 - abs(risk_score - 0.5) * 1.6))
    base_pass = max(0.02, 1.0 - base_fail - (base_flaky * 0.45))

    history_weight = min(0.45, len(runs) / 20.0)
    model_weight = 1.0 - history_weight
    probabilities = {
        "PASS": base_pass * model_weight + historical["passRate"] * history_weight,
        "FLAKY": base_flaky * model_weight + historical["flakyRate"] * history_weight,
        "FAIL": base_fail * model_weight + historical["failRate"] * history_weight,
    }
    total = sum(probabilities.values()) or 1.0
    return {key: round(value / total, 3) for key, value in probabilities.items()}


def predict_next_run(test_name: str) -> Dict[str, Any]:
    """
    Orchestrate loading history, extracting features, computing trends,
    scoring risk, and returning a prediction payload.
    """
    runs: List[Dict[str, Any]] = history.load_runs(test_name)
    return predict_from_runs(test_name, runs)


def predict_from_runs(test_name: str, runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build a prediction payload from preloaded historical runs.

    This avoids reloading history multiple times during an orchestrated request.
    """
    # runs are oldest->newest (per impl)
    if not runs:
        return {
            "testName": test_name,
            "riskScore": 0.0,
            "riskLevel": "LOW",
            "prediction": "PASS",
            "reasons": ["no_history"],
            "historyCount": 0,
            "history": [],
            "probabilities": {"PASS": 0.9, "FLAKY": 0.07, "FAIL": 0.03},
            "confidence": 0.35,
            "calibration": {"method": "cold_start_prior", "historyWeight": 0.0},
        }

    # extract features per run
    features_list = [extract_features(r) for r in runs]

    # trends computed across runs
    trends = analyze_trends(features_list)

    # pick the most recent run features as baseline for immediate indicators
    current_features = features_list[-1] if features_list else {}

    # compute risk
    risk_payload = compute_risk_score(current_features, trends)
    risk_score = float(risk_payload.get("riskScore", 0.0))
    probabilities = _calibrated_probabilities(risk_score, runs)
    history_weight = min(0.45, len(runs) / 20.0)

    # assemble full response
    response: Dict[str, Any] = {
        "testName": test_name,
        "historyCount": len(runs),
        "history": [_summarize_run(run, index + 1) for index, run in enumerate(runs)],
        "featuresCurrent": current_features,
        "trends": trends,
        "probabilities": probabilities,
        "confidence": round(0.5 + history_weight + min(0.1, len(risk_payload.get("reasons", [])) * 0.02), 3),
        "calibration": {
            "method": "risk_history_blend",
            "historyWeight": round(history_weight, 3),
            **_historical_outcome_rates(runs),
        },
        **risk_payload,
    }

    return response
