from pydantic import BaseModel, EmailStr
from typing import Optional, Literal, List
from datetime import datetime

class AuthUser(BaseModel):
    id: str
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    role: Literal["student", "instructor", "admin"] = "student"
    courses: List[str] = []
    email_confirmed: bool = False
    created_at: Optional[datetime] = None
    last_sign_in: Optional[datetime] = None

class GoogleTokenRequest(BaseModel):
    access_token: str
    account_type: Literal["student", "instructor"] = "student"

class AuthResponse(BaseModel):
    success: bool
    message: str
    user: Optional[AuthUser] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None

class RoleUpdateRequest(BaseModel):
    user_id: str
    new_role: Literal["student", "instructor", "admin"]

class AccountStatusRequest(BaseModel):
    user_id: str
    status: Literal["active", "blocked"]