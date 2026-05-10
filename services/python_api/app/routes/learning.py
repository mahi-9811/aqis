from __future__ import annotations

from fastapi import APIRouter, HTTPException

from aqis.learning.orchestrator import learning_stats, record_feedback
from aqis.learning.similarity_retriever import SimilarityRetriever
from services.python_api.app.schemas import FeedbackResponse, LearningSimilarResponse, LearningStatsResponse

router = APIRouter(prefix="/learning", tags=["learning"])
retriever = SimilarityRetriever()


@router.get("/similar/{test_name}", response_model=LearningSimilarResponse)
async def similar(test_name: str) -> LearningSimilarResponse:
    try:
        return retriever.retrieve_for_test(test_name)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/stats", response_model=LearningStatsResponse)
async def stats() -> LearningStatsResponse:
    try:
        return learning_stats()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/feedback", response_model=FeedbackResponse)
async def feedback(payload: dict[str, Any]) -> FeedbackResponse:
    try:
        return record_feedback(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
