# File: app/routers/advice.py

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.models import AdviceResponse
from app.services.advice import generate_advice   # ← point at advice.py!

router = APIRouter(prefix="/advice", tags=["advice"])

@router.get(
    "/{user_id}",
    response_model=AdviceResponse,
    summary="Get AI-generated workout advice for a user"
)
async def get_advice(
    user_id: str,
    limit: Optional[int] = Query(
        5, ge=1, le=20, description="How many past sessions to consider"
    )
):
    """
    Fetches the user's last `limit` workout sessions
    and returns personalized fitness advice.
    """
    try:
        advice_text = await generate_advice(user_id, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"advice": advice_text}
