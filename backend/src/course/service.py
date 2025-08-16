from fastapi import HTTPException, Request, status
from .CRUD import (
    create_course, update_course, delete_course, get_courses, get_course, get_all_courses, get_course_by_invite_code,
    find_course_by_title_ilike
)
from .models import CourseCreate, CourseUpdate, CourseResponse, CustomModel
from typing import List, Optional, Dict, Any
import random
from ..user.service import get_user_courses
from ..supabaseClient import supabase

# Retrieve the current user from session storage
def get_current_user(request: Request):
    user = request.session.get('session_user')
    if not user:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})
    return user

# Business logic functions using Supabase CRUD

def _generate_invite_code() -> str:
    # 6-digit numeric code as string, leading zeros allowed
    return f"{random.randint(0, 999999):06d}"


def create_course_service(created_by: str, course_data: CourseCreate) -> CourseResponse:
    """Create a new course with business logic validation"""
    try:
        # Generate a unique 6-digit invite code (retry a few times to avoid collisions)
        invite_code = _generate_invite_code()
        for _ in range(5):
            existing = supabase.table("courses").select("course_id").eq("invite_code", invite_code).execute()
            if not existing.data:
                break
            invite_code = _generate_invite_code()

        course = create_course(
            created_by=created_by,
            title=course_data.title,
            description=course_data.description,
            term=course_data.term,
            prompt=course_data.prompt,
            invite_code=invite_code
        )
        if not course:
            raise HTTPException(status_code=400, detail="Failed to create course")
        return CourseResponse(**course)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating course: {str(e)}")


def join_course_by_invite_code_service(user_id: str, invite_code: str) -> Dict[str, Any]:
    """Allow a user to join a course using a 6-digit invite code"""
    try:
        course = get_course_by_invite_code(invite_code)
        if not course:
            raise HTTPException(status_code=404, detail="Invalid invite code")

        # Add course to user via RPC
        supabase.rpc('add_course_to_user', {
            'user_uuid': str(user_id),
            'course_id': str(course['course_id'])
        }).execute()

        return {"success": True, "course_id": course["course_id"], "title": course.get("title")}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to join course: {str(e)}")

def get_course_service(course_id: str, user_id: str) -> CourseResponse:
    """Get a course with access validation"""
    try:
        course = get_course(course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        # Check if user has access to this course
        # Business rule: Users can access courses if they:
        # 1. Have the course in their courses list, OR
        # 2. Are the creator of the course (permanent access)
        try:
            user_courses = get_user_courses(user_id)
        except Exception as e:
            # If we can't get user courses, deny access
            raise HTTPException(status_code=403, detail="Cannot verify course access")
        
        if course_id not in user_courses and course['created_by'] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return CourseResponse(**course)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching course: {str(e)}")

def list_courses_service(user_id: str, limit: Optional[int] = None, 
                        offset: Optional[int] = None, search: Optional[str] = None) -> List[CourseResponse]:
    """Get all courses that a user has access to with optional filtering"""
    try:
        # Get user's courses
        user_courses = get_user_courses(user_id)
        
        # Get course details for each course ID
        courses = []
        for course_id in user_courses:
            course = get_course(course_id)
            if course:
                courses.append(course)
        
        # Apply search filter if provided
        if search:
            courses = [course for course in courses if search.lower() in course.get('title', '').lower()]
        
        # Apply pagination if provided
        if offset:
            courses = courses[offset:]
        if limit:
            courses = courses[:limit]
        
        return [CourseResponse(**course) for course in courses]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching courses: {str(e)}")

def join_course_by_title_service(user_id: str, title: str) -> dict:
    """Join a course by title with course lookup and validation"""
    try:
        course = find_course_by_title_ilike(title)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        from src.user.service import add_course_to_user
        added = add_course_to_user(user_id, course["course_id"])
        if not added:
            raise HTTPException(status_code=400, detail="Failed to join course")
        
        return {"success": True, "course": course}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error joining course: {str(e)}")

def update_course_service(course_id: str, user_id: str, course_data: CourseUpdate) -> CourseResponse:
    """Update a course with ownership validation"""
    # First check if course exists and user has access
    existing_course = get_course(course_id)
    if not existing_course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if existing_course['created_by'] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update the course
    try:
        update_data = {k: v for k, v in course_data.dict().items() if v is not None}
        updated_course = update_course(course_id, **update_data)
        if not updated_course:
            raise HTTPException(status_code=400, detail="Failed to update course")
        return CourseResponse(**updated_course)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating course: {str(e)}")

def delete_course_service(course_id: str, user_id: str) -> bool:
    """Delete a course with ownership validation"""
    # First check if course exists and user has access
    existing_course = get_course(course_id)
    if not existing_course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if existing_course['created_by'] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete the course
    try:
        result = delete_course(course_id)
        return bool(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting course: {str(e)}")

def get_course_count_service(user_id: str) -> Dict[str, int]:
    """Get course count for a user"""
    try:
        user_courses = get_user_courses(user_id)
        return {"count": len(user_courses)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting course count: {str(e)}")

def list_all_courses_service() -> List[CourseResponse]:
    """Get all courses - admin only"""
    try:
        courses = get_all_courses()
        return [CourseResponse(**course) for course in courses]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching all courses: {str(e)}")

def get_courses_by_user_service(user_id: str) -> List[CourseResponse]:
    """Get all courses that a specific user has access to"""
    try:
        user_courses = get_user_courses(user_id)
        courses = []
        for course_id in user_courses:
            course = get_course(course_id)
            if course:
                courses.append(course)
        return [CourseResponse(**course) for course in courses]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user courses: {str(e)}")

def list_my_courses_service(user_id: str, limit: Optional[int] = None, 
                           offset: Optional[int] = None, search: Optional[str] = None) -> List[CourseResponse]:
    """Get courses created by the current instructor with optional filtering"""
    try:
        courses = get_courses(user_id)
        
        # Apply search filter if provided
        if search:
            courses = [course for course in courses if search.lower() in (course.get('title') or '').lower()]
        
        # Apply pagination if provided
        if offset:
            courses = courses[offset:]
        if limit:
            courses = courses[:limit]
        
        return [CourseResponse(**course) for course in courses]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching courses: {str(e)}")

def add_custom_model_service(course_id: str, user_id: str, custom_model: CustomModel) -> Dict[str, Any]:
    """Add a custom model to a course"""
    try:
        # Check if course exists and user has access
        existing_course = get_course(course_id)
        if not existing_course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        if existing_course['created_by'] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get current custom models
        current_models = existing_course.get('custom_models', []) or []
        
        # Check if model name already exists
        for model in current_models:
            if model.get('name') == custom_model.name:
                raise HTTPException(status_code=400, detail="Model name already exists")
        
        # Add timestamp
        from datetime import datetime
        model_data = custom_model.dict()
        model_data['created_at'] = datetime.utcnow().isoformat()
        
        # Add new model
        current_models.append(model_data)
        
        # Update course
        updated_course = update_course(course_id, custom_models=current_models)
        if not updated_course:
            raise HTTPException(status_code=400, detail="Failed to add custom model")
        
        return {"success": True, "message": f"Custom model '{custom_model.name}' added successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding custom model: {str(e)}")

def get_custom_models_service(course_id: str, user_id: str) -> Dict[str, Any]:
    """Get custom models for a course"""
    try:
        # Check if course exists and user has access
        existing_course = get_course(course_id)
        if not existing_course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        # Check access (either creator or enrolled student)
        try:
            user_courses = get_user_courses(user_id)
        except Exception:
            user_courses = []
        
        if course_id not in user_courses and existing_course['created_by'] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        custom_models = existing_course.get('custom_models', []) or []
        
        # Remove API keys from response for security (only show to course creator)
        if existing_course['created_by'] != user_id:
            # For students, only return model names and types
            safe_models = []
            for model in custom_models:
                safe_models.append({
                    'name': model.get('name'),
                    'model_type': model.get('model_type'),
                    'created_at': model.get('created_at')
                })
            return {"custom_models": safe_models}
        
        return {"custom_models": custom_models}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching custom models: {str(e)}")

def delete_custom_model_service(course_id: str, user_id: str, model_name: str) -> Dict[str, Any]:
    """Delete a custom model from a course"""
    try:
        # Check if course exists and user has access
        existing_course = get_course(course_id)
        if not existing_course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        if existing_course['created_by'] != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get current custom models
        current_models = existing_course.get('custom_models', []) or []
        
        # Find and remove the model
        updated_models = [model for model in current_models if model.get('name') != model_name]
        
        if len(updated_models) == len(current_models):
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Update course
        updated_course = update_course(course_id, custom_models=updated_models)
        if not updated_course:
            raise HTTPException(status_code=400, detail="Failed to delete custom model")
        
        return {"success": True, "message": f"Custom model '{model_name}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting custom model: {str(e)}")