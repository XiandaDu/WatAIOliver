from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime

class ConversationBase(BaseModel):
    user_id: str
    sender: Literal["user", "assistant"]
    message: str

class ConversationCreate(ConversationBase):
    id: Optional[str] = None

class ConversationUpdate(BaseModel):
    conversation_id: str
    message: Optional[str] = None

class ConversationDelete(BaseModel):
    conversation_id: str

class MessageCreate(BaseModel):
    user_id: str    
    sender: Literal["user", "assistant"]
    content: str

class MessageUpdate(BaseModel):
    content: Optional[str] = None

class MessageDelete(BaseModel):
    message_id: str
