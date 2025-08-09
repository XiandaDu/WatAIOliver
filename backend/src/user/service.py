from fastapi import Depends, FastAPI, Request, UploadFile, File, Form, Query, HTTPException, status
from typing import List, Optional, Dict, Any
from .models import UserResponse, UserUpdate
from ..supabaseClient import supabase
import logging

logger = logging.getLogger(__name__)

def get_user_info(user_id: str) -> Optional[UserResponse]:
    """Get user information by user ID"""
    try:
        response = supabase.table("users").select("*").eq("user_id", user_id).execute()
        if response.data:
            user_data = response.data[0]
            return UserResponse(**user_data)
        return None
    except Exception as e:
        logger.error(f"Error getting user info for {user_id}: {e}")
        logger.error(f"Error details: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get user information: {str(e)}")

def update_user(user_id: str, user_data: UserUpdate) -> UserResponse:
    """Update user information"""
    try:
        update_data = {k: v for k, v in user_data.dict().items() if v is not None}
        
        response = supabase.table("users").update(update_data).eq("user_id", user_id).execute()
        if response.data:
            return UserResponse(**response.data[0])
        raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")

def add_course_to_user(user_id: str, course_id: str) -> bool:
    """Add a course to a user's course list"""
    try:
        # First check if course exists
        course_check = supabase.table("courses").select("course_id").eq("course_id", course_id).execute()
        if not course_check.data:
            raise HTTPException(status_code=404, detail="Course not found")
        
        # Use the database function to add course
        response = supabase.rpc('add_course_to_user', {
            'user_uuid': str(user_id),
            'course_id': str(course_id)
        }).execute()
        return True
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding course to user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add course to user: {str(e)}")

def remove_course_from_user(user_id: str, course_id: str) -> bool:
    """Remove a course from a user's course list"""
    try:
        # Use the database function to remove course
        response = supabase.rpc('remove_course_from_user', {
            'user_uuid': str(user_id),
            'course_id': str(course_id)
        }).execute()
        return True
    except Exception as e:
        logger.error(f"Error removing course from user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove course from user: {str(e)}")

def get_user_courses(user_id: str) -> List[str]:
    """Get all courses for a user"""
    try:
        # Use the database function to get user courses
        response = supabase.rpc('get_user_courses', {
            'user_uuid': str(user_id)
        }).execute()
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"Error getting user courses: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user courses: {str(e)}")

def get_users_by_course(course_id: str) -> List[UserResponse]:
    """Get all users who have access to a specific course"""
    try:
        response = supabase.table("users").select("*").contains("courses", [course_id]).execute()
        return [UserResponse(**user_data) for user_data in response.data]
    except Exception as e:
        logger.error(f"Error getting users by course {course_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get users by course: {str(e)}")

def get_all_users() -> List[UserResponse]:
    """Get all users (admin only)"""
    try:
        response = supabase.table("users").select("*").execute()
        return [UserResponse(**user_data) for user_data in response.data]
    except Exception as e:
        logger.error(f"Error getting all users: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get all users: {str(e)}")

def login():
    pass # need to implement uwaterloo SSO

def logout():
    pass # implement logout logic