from fastapi import FastAPI
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from fastapi import HTTPException
from users.CRUD import (
    create_user,
    get_users,
    get_user_by_id,
    update_user,
    delete_user,
)

app = FastAPI()

class UserCreate(BaseModel):
    user_id: str
    username: str
    email: str
    role: Optional[str] = "student"

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None

class User(BaseModel):
    user_id: str
    username: str
    email: EmailStr
    role: Optional[str] = "student"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@app.post("/users/", response_model=User)
def api_create_user(user: UserCreate):
    data = create_user(user.user_id, user.username, user.email, user.role)
    if data:
        return data[0]
    raise HTTPException(status_code=400, detail="User not created")

@app.get("/users/", response_model=List[User])
def api_get_users():
    data = get_users()
    return data

@app.get("/users/{user_id}", response_model=User)
def api_get_user_by_id(user_id: str):
    data = get_user_by_id(user_id)
    if data:
        return data[0]
    raise HTTPException(status_code=404, detail="User not found")

@app.put("/users/{user_id}", response_model=User)
def api_update_user(user_id: str, user: UserUpdate):
    data = update_user(user_id, user.username, user.email, user.role)
    if data:
        return data[0]
    raise HTTPException(status_code=404, detail="User not found")

@app.delete("/users/{user_id}")
def api_delete_user(user_id: str):
    data = delete_user(user_id)
    if data:
        return {"detail": "User deleted"}
    raise HTTPException(status_code=404, detail="User not found")
