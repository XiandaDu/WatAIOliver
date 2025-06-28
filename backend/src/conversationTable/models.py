from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ConversationCreate(BaseModel):
    conversation_id: Optional[str] = None  # Will be generated if not provided
    title: str
    user_id: Optional[str] = None

class ConversationUpdate(BaseModel):
    title: Optional[str] = None

class ConversationResponse(BaseModel):
    conversation_id: str
    title: str
    user_id: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]