from pathlib import Path

from aqis.agents.orchestrator import run_agents
from aqis.autofix.orchestrator import generate_autofix
from aqis.learning.embedding_generator import EmbeddingGenerator
from aqis.learning.knowledge_store import KnowledgeStore
from aqis.learning.orchestrator import retrieve_prior_knowledge, update_knowledge
from aqis.learning.similarity_retriever import SimilarityRetriever
from aqis.learning.vector_store import VectorStore
from aqis.learning import orchestrator as learning_orchestrator


def test_learning_update_and_retrieve_prior_knowledge(tmp_path: Path):
    bundle = {
        "testName": "sales_quote_search",
        "steps": [
            {
                "stepName": "Enter Sales Quotation value",
                "executedProperty": "xpath=//input[@id='quotation']",
                "timing": "240",
                "labels": ["Sales Quotation"],
                "errorMessage": "NoSuchElementException",
            }
        ],
        "exception": ["Exception: No such element found"],
        "retries": 2,
        "autoHeal": ["failed"],
        "driftSignals": ["locator_mismatch"],
        "ocrText": "Manage Sales Quotations\nSales Quotation",
        "raw": {"startlog": {"screenMismatch": True, "exceptions": ["sap.ui TimeoutException"]}},
    }
    risk_report = {"riskScore": 0.84, "riskLevel": "HIGH", "prediction": "FAIL"}
    agent_output = run_agents(bundle)
    autofix_output = generate_autofix(bundle, agent_output)

    store = KnowledgeStore(root=tmp_path / "knowledge")
    vectors = VectorStore(path=tmp_path / "vectors.json")
    embeddings = EmbeddingGenerator()
    retriever = SimilarityRetriever(store, embeddings, vectors)

    original_store = learning_orchestrator.knowledge_store
    original_vectors = learning_orchestrator.vector_store
    original_embeddings = learning_orchestrator.embedding_generator
    original_retriever = learning_orchestrator.similarity_retriever
    learning_orchestrator.knowledge_store = store
    learning_orchestrator.vector_store = vectors
    learning_orchestrator.embedding_generator = embeddings
    learning_orchestrator.similarity_retriever = retriever
    try:
        summary = update_knowledge(bundle, agent_output, autofix_output, risk_report=risk_report)
        retrieved = retrieve_prior_knowledge(bundle)
    finally:
        learning_orchestrator.knowledge_store = original_store
        learning_orchestrator.vector_store = original_vectors
        learning_orchestrator.embedding_generator = original_embeddings
        learning_orchestrator.similarity_retriever = original_retriever

    assert summary["testName"] == "sales_quote_search"
    assert store.load_knowledge("sales_quote_search")
    assert retrieved["similarCasesFound"] is True
    assert retrieved["matches"][0]["failureCategory"] is not None


def test_record_feedback_weights_confidence(tmp_path: Path):
    store = KnowledgeStore(root=tmp_path / "knowledge")
    original_store = learning_orchestrator.knowledge_store
    learning_orchestrator.knowledge_store = store
    try:
        result = learning_orchestrator.record_feedback(
            {
                "testName": "sales_quote_search",
                "fixOutcome": "success",
                "confidenceScore": 0.7,
                "fixType": "LOCATOR_UPDATE",
            }
        )
    finally:
        learning_orchestrator.knowledge_store = original_store

    assert result["feedbackWeight"] == 0.15
    assert result["entry"]["confidenceScore"] == 0.85
    assert result["entry"]["feedback"]["fixOutcome"] == "success"
