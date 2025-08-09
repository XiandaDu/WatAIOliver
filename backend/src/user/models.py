from pydantic import BaseModel
from typing import Literal, Optional, List
from datetime import datetime

class UserBase(BaseModel):
    user_id: str
    username: str
    email: str
    role: str
    courses: Optional[List[str]] = []
    created_at: datetime
    updated_at: datetime

class UserCreate(UserBase):
    id: Optional[str] = None

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    courses: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    role: str
    courses: List[str] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
