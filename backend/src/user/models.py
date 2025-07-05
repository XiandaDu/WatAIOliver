from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime

class UserBase(BaseModel):
    user_id: str
    nickname: str
    email: str
    role: str
    created_at: datetime
    updated_at: datetime

class UserCreate(UserBase):
    id: Optional[str] = None

class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
