from fastapi import HTTPException, Request, status
from .CRUD import (
    create_course, update_course, delete_course, get_courses, get_course, get_all_courses
)
from .models import CourseCreate, CourseUpdate, CourseResponse
from typing import List, Optional, Dict, Any
from ..user.service import get_user_courses
from ..supabaseClient import supabase

# Retrieve the current user from session storage
def get_current_user(request: Request):
    user = request.session.get('session_user')
    if not user:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})
    return user

# Business logic functions using Supabase CRUD

def create_course_service(created_by: str, course_data: CourseCreate) -> CourseResponse:
    """Create a new course with business logic validation"""
    try:
        course = create_course(
            created_by=created_by,
            title=course_data.title,
            description=course_data.description,
            term=course_data.term
        )
        if not course:
            raise HTTPException(status_code=400, detail="Failed to create course")
        return CourseResponse(**course)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating course: {str(e)}")

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