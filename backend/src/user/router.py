from fastapi import APIRouter, Request, UploadFile, File, Form, Query, HTTPException, status, Depends
from typing import List
from . import service
from .models import UserResponse, UserUpdate
from ..auth.middleware import get_current_user
from ..auth.models import AuthUser

router = APIRouter(
    prefix='/user',
    tags=['user']
)

@router.get("/", response_model=UserResponse)
async def get_user_info(current_user: AuthUser = Depends(get_current_user)):
    """Get current user information"""
    user = service.get_user_info(current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/", response_model=UserResponse)
async def update_user_info(user_data: UserUpdate, current_user: AuthUser = Depends(get_current_user)):
    """Update current user information"""
    user = service.update_user(current_user.id, user_data)
    return user

@router.get("/courses", response_model=List[str])
async def get_user_courses(current_user: AuthUser = Depends(get_current_user)):
    """Get all courses for the current user"""
    courses = service.get_user_courses(current_user.id)
    return courses

@router.post("/courses/{course_id}")
async def add_course_to_user(course_id: str, current_user: AuthUser = Depends(get_current_user)):
    """Add a course to the current user"""
    success = service.add_course_to_user(current_user.id, course_id)
    return {"success": success, "message": "Course added successfully"}

@router.delete("/courses/{course_id}")
async def remove_course_from_user(course_id: str, current_user: AuthUser = Depends(get_current_user)):
    """Remove a course from the current user"""
    success = service.remove_course_from_user(current_user.id, course_id)
    return {"success": success, "message": "Course removed successfully"}

@router.get("/all", response_model=List[UserResponse])
async def get_all_users(current_user: AuthUser = Depends(get_current_user)):
    """Get all users (admin only)"""
    # Check if user is admin
    user = service.get_user_info(current_user.id)
    if not user or user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = service.get_all_users()
    return users

@router.get("/by-course/{course_id}", response_model=List[UserResponse])
async def get_users_by_course(course_id: str, current_user: AuthUser = Depends(get_current_user)):
    """Get all users who have access to a specific course (admin only)"""
    # Check if user is admin
    user = service.get_user_info(current_user.id)
    if not user or user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = service.get_users_by_course(course_id)
    return users

@router.get("/login")
async def login():
    return service.login()

@router.get("/logout")
async def logout():
    return service.logout()






