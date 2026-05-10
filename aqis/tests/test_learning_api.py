import asyncio
from pathlib import Path

from aqis.agents.orchestrator import run_agents
from aqis.autofix.orchestrator import generate_autofix
from aqis.learning.embedding_generator import EmbeddingGenerator
from aqis.learning.knowledge_store import KnowledgeStore
from aqis.learning.similarity_retriever import SimilarityRetriever
from aqis.learning.vector_store import VectorStore
from aqis.learning import orchestrator as learning_orchestrator
from services.python_api.app.routes import learning as learning_route


def test_learning_endpoints_return_stats_and_similar_cases(tmp_path: Path):
    bundle = {
        "testName": "login_test",
        "steps": [
            {
                "stepName": "Open Login",
                "executedProperty": "id=username",
                "timing": "100",
                "labels": ["Username"],
                "errorMessage": "NoSuchElementException",
            }
        ],
        "exception": ["No such element"],
        "retries": 1,
        "autoHeal": [],
        "driftSignals": [],
        "ocrText": "Login Username Password",
        "raw": {"startlog": {"screenMismatch": False, "exceptions": []}},
    }
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
    original_route_retriever = learning_route.retriever
    learning_orchestrator.knowledge_store = store
    learning_orchestrator.vector_store = vectors
    learning_orchestrator.embedding_generator = embeddings
    learning_orchestrator.similarity_retriever = retriever
    learning_route.retriever = retriever
    try:
        learning_orchestrator.update_knowledge(bundle, agent_output, autofix_output, risk_report={"riskScore": 0.2, "riskLevel": "LOW"})
        stats_payload = asyncio.run(learning_route.stats())
        similar_payload = asyncio.run(learning_route.similar("login_test"))
        feedback_payload = asyncio.run(
            learning_route.feedback(
                {
                    "testName": "login_test",
                    "fixType": "locator",
                    "fixOutcome": "success",
                    "recommended": True,
                    "confidenceScore": 0.88,
                }
            )
        )
    finally:
        learning_orchestrator.knowledge_store = original_store
        learning_orchestrator.vector_store = original_vectors
        learning_orchestrator.embedding_generator = original_embeddings
        learning_orchestrator.similarity_retriever = original_retriever
        learning_route.retriever = original_route_retriever

    assert stats_payload["storedRuns"] >= 1
    assert similar_payload["similarCasesFound"] is True
    assert feedback_payload["stored"] is True
