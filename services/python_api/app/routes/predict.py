from fastapi import APIRouter, HTTPException

from aqis.risk_engine.prediction_engine import predict_next_run
from services.python_api.app.schemas import PredictionResponse

router = APIRouter(prefix="/predict", tags=["predict"])


@router.get("/{test_name}", response_model=PredictionResponse)
async def predict(test_name: str) -> PredictionResponse:
    try:
        return predict_next_run(test_name)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
