from __future__ import annotations

import asyncio
import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aqis.agents.orchestrator import run_agents
from aqis.autofix.orchestrator import generate_autofix
from aqis.core.logger import setup_logger
from aqis.learning.orchestrator import retrieve_prior_knowledge, update_knowledge
from aqis.parser.bundle_normalizer import build_failure_bundle
from aqis.parser.screenshot_ocr import extract_ocr
from aqis.parser.startlog_parser import parse_startlog
from aqis.parser.xml_parser import parse_xml
from aqis.risk_engine.feature_extractor import extract_features
from aqis.risk_engine.history_manager import RunHistoryManager
from aqis.risk_engine.prediction_engine import predict_from_runs
from aqis.testgen.orchestrator import generate_test_cases

logger = setup_logger("aqis.orchestration")
history_manager = RunHistoryManager()
_XML_CACHE: dict[str, dict[str, Any]] = {}
_STARTLOG_CACHE: dict[str, dict[str, Any]] = {}
_OCR_CACHE: dict[str, dict[str, Any]] = {}


@dataclass
class ParsedArtifacts:
    bundle: dict[str, Any]
    uploaded_artifacts: dict[str, Any]
    parse_timings: dict[str, float]


async def analyze_uploaded_artifacts(
    *,
    xml_bytes: bytes,
    startlog_bytes: bytes,
    screenshot_bytes_list: list[bytes] | None,
    test_name: str | None,
    filenames: dict[str, Any],
) -> dict[str, Any]:
    started_at = time.perf_counter()
    parsed = await parse_uploaded_artifacts(
        xml_bytes=xml_bytes,
        startlog_bytes=startlog_bytes,
        screenshot_bytes_list=screenshot_bytes_list,
        test_name=test_name,
        filenames=filenames,
    )
    response = build_unified_response(bundle=parsed.bundle, uploaded_artifacts=parsed.uploaded_artifacts)
    response["diagnostics"]["phaseTimings"].update(parsed.parse_timings)
    response["diagnostics"]["phaseTimings"]["totalAnalyzeSeconds"] = round(time.perf_counter() - started_at, 4)
    return response


def analyze_bundle(bundle: dict[str, Any], uploaded_artifacts: dict[str, Any] | None = None) -> dict[str, Any]:
    started_at = time.perf_counter()
    response = build_unified_response(bundle=bundle, uploaded_artifacts=uploaded_artifacts or {})
    response["diagnostics"]["phaseTimings"]["totalAnalyzeSeconds"] = round(time.perf_counter() - started_at, 4)
    return response


async def parse_uploaded_artifacts(
    *,
    xml_bytes: bytes,
    startlog_bytes: bytes,
    screenshot_bytes_list: list[bytes] | None,
    test_name: str | None,
    filenames: dict[str, Any],
) -> ParsedArtifacts:
    parse_timings: dict[str, float] = {}
    xml_started = time.perf_counter()
    try:
        xml_data = await asyncio.wait_for(
            asyncio.to_thread(_parse_xml_cached, xml_bytes),
            timeout=2.0,
        )
    except asyncio.TimeoutError as exc:
        raise ValueError("log.xml parsing timed out.") from exc
    parse_timings["xmlParseSeconds"] = round(time.perf_counter() - xml_started, 4)
    if "error" in xml_data:
        raise ValueError(f"Corrupt log.xml: {xml_data['error']}")

    startlog_started = time.perf_counter()
    try:
        startlog_data = await asyncio.wait_for(
            asyncio.to_thread(_parse_startlog_cached, startlog_bytes),
            timeout=2.0,
        )
    except asyncio.TimeoutError as exc:
        raise ValueError("STARTLog.txt parsing timed out.") from exc
    parse_timings["startlogParseSeconds"] = round(time.perf_counter() - startlog_started, 4)

    ocr_started = time.perf_counter()
    screenshot_bytes_list = screenshot_bytes_list or []
    if screenshot_bytes_list:
        try:
            ocr_payloads = await asyncio.wait_for(
                asyncio.gather(
                    *[
                        asyncio.to_thread(_extract_ocr_cached, screenshot_bytes)
                        for screenshot_bytes in screenshot_bytes_list
                    ]
                ),
                timeout=5.0,
            )
            ocr_data = {
                "ocrText": "\n\n".join(
                    payload.get("ocrText", "")
                    for payload in ocr_payloads
                    if payload.get("ocrText")
                )
            }
        except asyncio.TimeoutError:
            logger.warning("ocr_timeout screenshot_count=%s", len(screenshot_bytes_list))
            ocr_data = {"ocrText": "", "warning": "OCR timed out and was skipped."}
    else:
        ocr_data = {"ocrText": ""}
    parse_timings["ocrSeconds"] = round(time.perf_counter() - ocr_started, 4)

    bundle = build_failure_bundle(xml_data, startlog_data, ocr_data)
    resolved_test_name = _resolve_test_name(
        explicit_test_name=test_name,
        bundle_test_name=bundle.get("testName"),
        filenames=filenames,
    )
    if not resolved_test_name:
        raise ValueError("Test name could not be resolved from the upload. Provide testName or include TestName in log.xml.")

    bundle["testName"] = resolved_test_name
    return ParsedArtifacts(
        bundle=bundle,
        uploaded_artifacts={
            "logXml": filenames.get("logXml"),
            "startLog": filenames.get("startLog"),
            "screenshots": filenames.get("screenshots", []),
            "screenshotCount": len(screenshot_bytes_list),
            "screenshotProvided": bool(screenshot_bytes_list),
            "ocrWarning": ocr_data.get("warning"),
        },
        parse_timings=parse_timings,
    )


def _resolve_test_name(
    *,
    explicit_test_name: str | None,
    bundle_test_name: Any,
    filenames: dict[str, Any],
) -> str:
    candidates = [
        explicit_test_name,
        str(bundle_test_name or ""),
        _derive_test_name_from_filename(filenames.get("logXml")),
        _derive_test_name_from_filename(filenames.get("startLog")),
    ]
    for candidate in candidates:
        normalized = str(candidate or "").strip()
        if normalized:
            return normalized
    return ""


def _derive_test_name_from_filename(filename: Any) -> str:
    raw_name = str(filename or "").strip()
    if not raw_name:
        return ""

    stem = Path(raw_name).stem.strip()
    if not stem:
        return ""

    generic_names = {"log", "log.xml", "startlog", "startlog.txt", "screenshot", "image"}
    if stem.lower() in generic_names:
        return ""

    return stem


def build_unified_response(bundle: dict[str, Any], uploaded_artifacts: dict[str, Any]) -> dict[str, Any]:
    test_name = str(bundle.get("testName") or "").strip()
    if not test_name:
        raise ValueError("bundle must include testName")

    timings: dict[str, float] = {}
    load_started = time.perf_counter()
    historical_runs = history_manager.load_runs(test_name)
    timings["historyLoadSeconds"] = round(time.perf_counter() - load_started, 4)

    persist_started = time.perf_counter()
    current_run_saved = False
    if not _history_already_contains_bundle(historical_runs, bundle):
        history_manager.save_run(bundle, test_name)
        historical_runs = history_manager.load_runs(test_name)
        current_run_saved = True
    timings["historyPersistSeconds"] = round(time.perf_counter() - persist_started, 4)

    prediction_started = time.perf_counter()
    prediction = predict_from_runs(test_name, historical_runs)
    timings["predictionSeconds"] = round(time.perf_counter() - prediction_started, 4)

    learning_started = time.perf_counter()
    prior_knowledge = retrieve_prior_knowledge(bundle)
    timings["learningRetrieveSeconds"] = round(time.perf_counter() - learning_started, 4)

    analysis_started = time.perf_counter()
    root_cause_analysis = run_agents(bundle)
    timings["agentAnalysisSeconds"] = round(time.perf_counter() - analysis_started, 4)

    autofix_started = time.perf_counter()
    auto_fix = generate_autofix(bundle, root_cause_analysis)
    timings["autofixSeconds"] = round(time.perf_counter() - autofix_started, 4)

    testgen_started = time.perf_counter()
    generated_test_cases = generate_test_cases(bundle, prediction, root_cause_analysis, auto_fix)
    timings["testgenSeconds"] = round(time.perf_counter() - testgen_started, 4)

    learning_update_started = time.perf_counter()
    knowledge_record = update_knowledge(
        bundle,
        root_cause_analysis,
        auto_fix,
        risk_report=prediction,
        generated_tests=generated_test_cases,
    )
    timings["learningUpdateSeconds"] = round(time.perf_counter() - learning_update_started, 4)

    features = extract_features(bundle)
    warnings = _build_warnings(prediction, auto_fix, uploaded_artifacts)
    response = {
        "testSummary": {
            "testName": test_name,
            "uiContext": root_cause_analysis.get("agents", {}).get("testReader", {}).get("uiContext"),
            "stepSummary": root_cause_analysis.get("agents", {}).get("testReader", {}).get("stepSummary"),
            "historyCount": prediction.get("historyCount", 0),
            "currentRunStored": current_run_saved,
            "uploadedArtifacts": uploaded_artifacts,
            "screenshotAvailable": bool(uploaded_artifacts.get("screenshotProvided")),
            "ocrText": bundle.get("ocrText", ""),
            "failureCategory": root_cause_analysis.get("agents", {}).get("failureAnalyzer", {}).get("failureCategory"),
        },
        "prediction": _normalize_prediction(prediction),
        "rootCauseAnalysis": {
            "summary": root_cause_analysis.get("finalReport", {}),
            "details": root_cause_analysis.get("agents", {}),
            "priorKnowledge": prior_knowledge,
        },
        "autoFix": _normalize_autofix(auto_fix),
        "generatedTestCases": generated_test_cases,
        "trendSummary": {
            "timingSlope": prediction.get("trends", {}).get("timingSlope", 0.0),
            "retryTrend": prediction.get("trends", {}).get("retryTrend", "stable"),
            "driftTrend": prediction.get("trends", {}).get("driftTrend", "stable"),
            "uiErrorSpike": prediction.get("trends", {}).get("uiErrorSpike", False),
            "riskScoreOverTime": [prediction.get("riskScore", 0.0)],
            "featureSnapshot": features,
        },
        "nextRunRecommendation": _next_run_recommendation(prediction, auto_fix, generated_test_cases),
        "warnings": warnings,
        "diagnostics": {
            "phaseTimings": timings,
            "knowledgeRecordId": knowledge_record.get("id"),
        },
        "bundle": bundle,
    }

    logger.info(
        "analyze_complete test=%s risk=%s prediction=%s warnings=%s timings=%s",
        test_name,
        response["prediction"]["riskLevel"],
        response["prediction"]["prediction"],
        warnings,
        timings,
    )
    return response


def _normalize_prediction(prediction: dict[str, Any]) -> dict[str, Any]:
    history_count = int(prediction.get("historyCount", 0))
    available = history_count >= 2
    message = "Prediction available."
    if not available:
        message = "Prediction unavailable — insufficient run history."

    return {
        **prediction,
        "available": available,
        "message": message,
    }


def _normalize_autofix(auto_fix: dict[str, Any]) -> dict[str, Any]:
    if auto_fix.get("recommended"):
        message = "AutoFix candidates are available for review."
    else:
        message = "AutoFix not recommended for this failure type."
    return {
        **auto_fix,
        "message": message,
    }


def _next_run_recommendation(
    prediction: dict[str, Any],
    auto_fix: dict[str, Any],
    generated_test_cases: dict[str, Any],
) -> str:
    if not prediction.get("available"):
        return "Collect at least one more completed run to enable a confident next-run prediction."
    if prediction.get("riskLevel") == "HIGH":
        return "Apply the approved fixes and add HIGH priority preventive tests before the next run."
    if auto_fix.get("recommended"):
        return "Validate the recommended AutoFix and then run the new preventive tests."
    return generated_test_cases.get("recommendation", "Review the generated test cases before the next run.")


def _build_warnings(
    prediction: dict[str, Any],
    auto_fix: dict[str, Any],
    uploaded_artifacts: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []
    if not uploaded_artifacts.get("screenshotProvided"):
        warnings.append("Screenshot not provided — OCR insights may be limited.")
    if uploaded_artifacts.get("ocrWarning"):
        warnings.append(str(uploaded_artifacts["ocrWarning"]))
    if not prediction.get("available"):
        warnings.append("Prediction unavailable — insufficient run history.")
    if not auto_fix.get("recommended"):
        warnings.append("AutoFix not recommended for this failure type.")
    return warnings


def _history_already_contains_bundle(runs: list[dict[str, Any]], bundle: dict[str, Any]) -> bool:
    if not runs:
        return False
    latest = runs[-1]
    return (
        latest.get("testName") == bundle.get("testName")
        and latest.get("steps") == bundle.get("steps")
        and latest.get("exception") == bundle.get("exception")
        and latest.get("retries") == bundle.get("retries")
        and latest.get("ocrText") == bundle.get("ocrText")
    )


def _cache_key(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _parse_xml_cached(xml_bytes: bytes) -> dict[str, Any]:
    key = _cache_key(xml_bytes)
    if key not in _XML_CACHE:
        _XML_CACHE[key] = parse_xml(xml_bytes)
    return dict(_XML_CACHE[key])


def _parse_startlog_cached(startlog_bytes: bytes) -> dict[str, Any]:
    key = _cache_key(startlog_bytes)
    if key not in _STARTLOG_CACHE:
        text = startlog_bytes.decode("utf-8", errors="replace")
        _STARTLOG_CACHE[key] = parse_startlog(text)
    return dict(_STARTLOG_CACHE[key])


def _extract_ocr_cached(screenshot_bytes: bytes) -> dict[str, Any]:
    key = _cache_key(screenshot_bytes)
    if key not in _OCR_CACHE:
        _OCR_CACHE[key] = extract_ocr(screenshot_bytes)
    return dict(_OCR_CACHE[key])
