from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MessageCreate(BaseModel):
    message_id: str
    user_id: Optional[str] = None
    content: str
    sender: str
    conversation_id: str  # Changed to string to match frontend usage
    course_id: Optional[str] = None
    model: Optional[str] = None

class MessageUpdate(BaseModel):
    content: Optional[str] = None

class MessageResponse(BaseModel):
    message_id: str
    user_id: Optional[str]
    content: str
    sender: str
    conversation_id: str  # Changed to string to match frontend usage
    course_id: Optional[str] = None
    model: Optional[str] = None
    created_at: Optional[datetime]
    updated_at: Optional[datetime]