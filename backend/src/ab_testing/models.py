from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class ABTestCreateRequest(BaseModel):
    query: str
    user_id: UUID
    course_id: Optional[UUID] = None
    interaction_mode: str  # 'daily' or 'problem_solving'

class ABTestFeedback(BaseModel):
    query_id: UUID
    chosen_response_id: str  # 'A' or 'B'
    feedback_text: Optional[str] = None

class ABTestResponse(BaseModel):
    query_id: UUID
    response_a: str
    response_b: str
    metadata: dict