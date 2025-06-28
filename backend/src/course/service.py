from fastapi import HTTPException, Request, status
from .CRUD import (
    create_course, get_courses, get_courses_by_user, get_all_courses,
    update_course, delete_course, search_courses, get_course_count
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

def create_course_service(user_id: int, course_data: CourseCreate) -> CourseResponse:
    """Create a new course with business logic validation"""
    try:
        course = create_course(
            user_id=user_id,
            name=course_data.name,
            notes=course_data.notes,
            doc=course_data.doc,
            model=course_data.model,
            prompt=course_data.prompt
        )
        if not course:
            raise HTTPException(status_code=400, detail="Failed to create course")
        return CourseResponse(**course)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating course: {str(e)}")

def get_course_service(course_id: int, user_id: int) -> CourseResponse:
    """Get a course with ownership validation"""
    course = get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if course['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return CourseResponse(**course)

def list_courses_service(user_id: int, limit: Optional[int] = None, 
                        offset: Optional[int] = None, search: Optional[str] = None) -> List[CourseResponse]:
    """Get courses for a user with optional filtering and pagination"""
    try:
        if search:
            courses = search_courses(user_id, search)
        else:
            courses = get_courses_by_user(user_id)
        
        # Apply pagination
        if offset:
            courses = courses[offset:]
        if limit:
            courses = courses[:limit]
        
        return [CourseResponse(**course) for course in courses]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching courses: {str(e)}")

def update_course_service(course_id: int, user_id: int, course_data: CourseUpdate) -> CourseResponse:
    """Update a course with ownership validation"""
    # Check ownership first
    existing_course = get_course(course_id)
    if not existing_course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if existing_course['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        update_data = course_data.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        updated_course = update_course(course_id, **update_data)
        if not updated_course:
            raise HTTPException(status_code=400, detail="Failed to update course")
        
        return CourseResponse(**updated_course)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating course: {str(e)}")

def delete_course_service(course_id: int, user_id: int) -> bool:
    """Delete a course with ownership validation"""
    # Check ownership first
    existing_course = get_course(course_id)
    if not existing_course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if existing_course['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        success = delete_course(course_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to delete course")
        return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting course: {str(e)}")

def get_course_count_service(user_id: int) -> Dict[str, int]:
    """Get course count for a user"""
    try:
        count = get_course_count(user_id)
        return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting course count: {str(e)}")