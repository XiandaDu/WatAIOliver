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
    message: Optional[str] = None
    reasoning: Optional[bool] = None

class ConversationOut(ConversationBase):
    id: str
    created_at: datetime
    updated_at: datetime
