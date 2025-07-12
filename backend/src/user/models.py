from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime

class UserBase(BaseModel):
    user_id: str
    username: str  # Changed from nickname to username
    email: str
    role: str = "student"  # Default to student
    created_at: Optional[datetime] = None  # Make optional since DB has default
    updated_at: Optional[datetime] = None  # Make optional since DB has default

class UserCreate(BaseModel):
    user_id: str
    username: str  # Changed from nickname to username
    email: str
    role: str = "student"
    # No need to pass created_at/updated_at as they're defaulted in the DB

class UserUpdate(BaseModel):
    username: Optional[str] = None  # Changed from nickname to username
    email: Optional[str] = None
    role: Optional[str] = None
