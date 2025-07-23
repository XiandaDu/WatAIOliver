from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime

class ConversationBase(BaseModel):
    conversation_id: str
    user_id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class ConversationCreate(BaseModel):
    user_id: str
    title: Optional[str] = None

class ConversationUpdate(BaseModel):
    conversation_id: str
    title: Optional[str] = None

class ChatRequest(BaseModel):
    prompt: str
    conversation_id: Optional[str] = None
    file_context: Optional[str] = None
    model: Optional[str] = "qwen3"
    course_id: Optional[str] = None

class ConversationDelete(BaseModel):
    conversation_id: str

class ConversationOut(BaseModel):
    data: list[ConversationBase]
    count: Optional[int] = None

class MessageBase(BaseModel):
    message_id: str
    conversation_id: str
    user_id: str
    sender: Literal["user", "assistant"]
    content: str
    created_at: datetime
    updated_at: datetime

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

class MessageOut(BaseModel):
    data: list[MessageBase]
    count: Optional[int] = None