from pathlib import Path

from fastapi.testclient import TestClient

from aqis.learning.embedding_generator import EmbeddingGenerator
from aqis.learning.knowledge_store import KnowledgeStore
from aqis.learning.similarity_retriever import SimilarityRetriever
from aqis.learning.vector_store import VectorStore
from aqis.learning import orchestrator as learning_orchestrator
from aqis.risk_engine.history_manager import RunHistoryManager
from services.python_api.app.main import app
from services.python_api.app.services import orchestration


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "analyze_sample"


def test_post_analyze_end_to_end_with_multiple_screenshots(tmp_path):
    manager = RunHistoryManager(root=tmp_path / "history")
    prior_bundle = {
        "testName": "sales_quote_search",
        "steps": [
            {
                "stepName": "Enter Sales Quotation value",
                "executedProperty": "id=quotation-input",
                "timing": "190",
                "labels": ["Sales Quotation"],
                "errorMessage": "",
            }
        ],
        "exception": [],
        "retries": 0,
        "autoHeal": [],
        "driftSignals": [],
        "ocrText": "Manage Sales Quotations\nSales Quotation",
        "raw": {"startlog": {"screenMismatch": False, "exceptions": []}},
    }
    manager.save_run(prior_bundle, "sales_quote_search")

    store = KnowledgeStore(root=tmp_path / "knowledge")
    vectors = VectorStore(path=tmp_path / "vectors.json")
    embeddings = EmbeddingGenerator()
    retriever = SimilarityRetriever(store, embeddings, vectors)

    original_history = orchestration.history_manager
    original_ocr = orchestration._extract_ocr_cached
    original_store = learning_orchestrator.knowledge_store
    original_vectors = learning_orchestrator.vector_store
    original_embeddings = learning_orchestrator.embedding_generator
    original_retriever = learning_orchestrator.similarity_retriever

    ocr_results = iter(
        [
            {"ocrText": "Manage Sales Quotations"},
            {"ocrText": "Sales Quotation Go"},
        ]
    )

    orchestration.history_manager = manager
    orchestration._extract_ocr_cached = lambda _bytes: next(ocr_results)
    learning_orchestrator.knowledge_store = store
    learning_orchestrator.vector_store = vectors
    learning_orchestrator.embedding_generator = embeddings
    learning_orchestrator.similarity_retriever = retriever

    client = TestClient(app)
    try:
        with (
            (FIXTURES / "log.xml").open("rb") as log_xml,
            (FIXTURES / "STARTLog.txt").open("rb") as start_log,
            (FIXTURES / "screen_1.png").open("rb") as screen_one,
            (FIXTURES / "screen_2.png").open("rb") as screen_two,
        ):
            response = client.post(
                "/analyze",
                files=[
                    ("logXml", ("log.xml", log_xml, "text/xml")),
                    ("startLog", ("STARTLog.txt", start_log, "text/plain")),
                    ("screenshot", ("screen_1.png", screen_one, "image/png")),
                    ("screenshot", ("screen_2.png", screen_two, "image/png")),
                ],
            )
    finally:
        orchestration.history_manager = original_history
        orchestration._extract_ocr_cached = original_ocr
        learning_orchestrator.knowledge_store = original_store
        learning_orchestrator.vector_store = original_vectors
        learning_orchestrator.embedding_generator = original_embeddings
        learning_orchestrator.similarity_retriever = original_retriever

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) >= {
        "testSummary",
        "prediction",
        "rootCauseAnalysis",
        "autoFix",
        "generatedTestCases",
        "trendSummary",
        "nextRunRecommendation",
    }
    assert payload["testSummary"]["testName"] == "sales_quote_search"
    assert payload["testSummary"]["uploadedArtifacts"]["screenshotCount"] == 2
    assert payload["testSummary"]["uploadedArtifacts"]["screenshots"] == ["screen_1.png", "screen_2.png"]
    assert payload["prediction"]["available"] is True
    assert "Sales Quotation Go" in payload["testSummary"]["ocrText"]
    assert "priorKnowledge" in payload["rootCauseAnalysis"]
    assert "phaseTimings" in payload["diagnostics"]


def test_post_analyze_accepts_folder_upload_relative_paths(tmp_path):
    manager = RunHistoryManager(root=tmp_path / "history")
    prior_bundle = {
        "testName": "sales_quote_search",
        "steps": [{"stepName": "Open", "executedProperty": "id=page", "timing": "100", "labels": [], "errorMessage": ""}],
        "exception": [],
        "retries": 0,
        "autoHeal": [],
        "driftSignals": [],
        "ocrText": "",
        "raw": {"startlog": {"screenMismatch": False, "exceptions": []}},
    }
    manager.save_run(prior_bundle, "sales_quote_search")

    original_history = orchestration.history_manager
    original_ocr = orchestration._extract_ocr_cached
    orchestration.history_manager = manager
    orchestration._extract_ocr_cached = lambda _bytes: {"ocrText": "Folder upload screenshot"}

    client = TestClient(app)
    try:
        with (
            (FIXTURES / "log.xml").open("rb") as log_xml,
            (FIXTURES / "STARTLog.txt").open("rb") as start_log,
            (FIXTURES / "screen_1.png").open("rb") as screen_one,
        ):
            response = client.post(
                "/analyze",
                files=[
                    ("logXml", ("MSQ_20260224135941/log.xml", log_xml, "text/xml")),
                    ("startLog", ("MSQ_20260224135941/STARTLog.txt", start_log, "text/plain")),
                    ("screenshot", ("MSQ_20260224135941/screen_1.png", screen_one, "image/png")),
                ],
            )
    finally:
        orchestration.history_manager = original_history
        orchestration._extract_ocr_cached = original_ocr

    assert response.status_code == 200
    payload = response.json()
    assert payload["testSummary"]["uploadedArtifacts"]["logXml"] == "log.xml"
    assert payload["testSummary"]["uploadedArtifacts"]["startLog"] == "STARTLog.txt"
    assert payload["testSummary"]["uploadedArtifacts"]["screenshots"] == ["screen_1.png"]
