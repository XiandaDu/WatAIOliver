from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime

class ConversationCreate(BaseModel):
    user_id: str
    title: Optional[str] = None

class ConversationUpdate(BaseModel):
    conversation_id: str
    title: Optional[str] = None

class ConversationDelete(BaseModel):
    conversation_id: str

class MessageCreate(BaseModel):
    conversation_id: str
    user_id: str    
    sender: Literal["user", "assistant"]
    content: str

class MessageUpdate(BaseModel):
    message_id: str
    content: Optional[str] = None

class MessageDelete(BaseModel):
    message_id: str
