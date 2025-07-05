from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MessageCreate(BaseModel):
    message_id: str
    user_id: Optional[str] = None
    content: str
    sender: str
    conversation_id: int

class MessageUpdate(BaseModel):
    content: Optional[str] = None

class MessageResponse(BaseModel):
    message_id: str
    user_id: Optional[str]
    content: str
    sender: str
    conversation_id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]