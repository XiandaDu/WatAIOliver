from fastapi import APIRouter, HTTPException
from .models import ABTestFeedback, ABTestCreateRequest, ABTestResponse
from .service import submit_ab_test_feedback, create_ab_test_query
from typing import UUID

router = APIRouter(
    prefix='/api/ab_test',
    tags=['ab-testing']
)

@router.post("/create")
async def create_ab_test_api(request: ABTestCreateRequest):
    """Create A/B test with two prompt variants for a user query"""
    try:
        result = await create_ab_test_query(
            user_query=request.query,
            user_id=request.user_id,
            course_id=request.course_id,
            interaction_mode=request.interaction_mode
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/feedback")
async def submit_feedback_api(feedback: ABTestFeedback):
    """Submit user's choice and feedback for A/B test"""
    try:
        result = await submit_ab_test_feedback(feedback)
        return {"status": "success", "message": "Feedback recorded"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))