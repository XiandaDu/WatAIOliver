from fastapi import HTTPException, Request, status
from .CRUD import (
    create_course, update_course, delete_course, get_courses, get_course, get_all_courses
)
from .models import CourseCreate, CourseUpdate, CourseResponse
from typing import List, Optional, Dict, Any

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

def get_course_service(course_id: str, created_by: str) -> CourseResponse:
    """Get a course with ownership validation"""
    course = get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if course['created_by'] != created_by:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return CourseResponse(**course)

def list_courses_service(created_by: str, limit: Optional[int] = None, 
                        offset: Optional[int] = None, search: Optional[str] = None) -> List[CourseResponse]:
    """Get all courses for a user with optional filtering"""
    try:
        courses = get_courses(created_by)
        
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

def update_course_service(course_id: str, created_by: str, course_data: CourseUpdate) -> CourseResponse:
    """Update a course with ownership validation"""
    # First check if course exists and user has access
    existing_course = get_course(course_id)
    if not existing_course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if existing_course['created_by'] != created_by:
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

def delete_course_service(course_id: str, created_by: str) -> bool:
    """Delete a course with ownership validation"""
    # First check if course exists and user has access
    existing_course = get_course(course_id)
    if not existing_course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if existing_course['created_by'] != created_by:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete the course
    try:
        result = delete_course(course_id)
        return bool(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting course: {str(e)}")

def get_course_count_service(created_by: str) -> Dict[str, int]:
    """Get course count for a user"""
    try:
        from .CRUD import get_course_count
        count = get_course_count(created_by)
        return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting course count: {str(e)}")

def list_all_courses_service() -> List[CourseResponse]:
    """Get all courses - admin only"""
    try:
        courses = get_all_courses()
        return [CourseResponse(**course) for course in courses]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching all courses: {str(e)}")