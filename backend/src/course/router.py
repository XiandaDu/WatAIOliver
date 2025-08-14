from fastapi import APIRouter, Request, Depends, HTTPException, Query, status, Form
from . import service
from .CRUD import (
    create_course, get_course, get_courses, get_all_courses,
    search_courses, get_course_count, update_course, delete_course
)
from .models import CourseCreate, CourseUpdate, CourseResponse
from typing import List, Optional

from datetime import datetime
from src.auth.middleware import auth_required, get_current_user, instructor_required
from src.auth.models import AuthUser


router = APIRouter(
    prefix='/course',
    tags=['course']
)

# REST API Endpoints using Supabase

@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course_api(
    course_data: CourseCreate,
    current_user: AuthUser = Depends(get_current_user)
):
    """Create a new course"""
    try:
        course = service.create_course_service(
            created_by=current_user.id,
            course_data=course_data
        )
        return course
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating course: {str(e)}")

@router.get("/my-courses", response_model=List[CourseResponse])
async def list_my_courses_api(
    current_user: AuthUser = Depends(instructor_required),
    limit: Optional[int] = Query(100, ge=1, le=1000),
    offset: Optional[int] = Query(0, ge=0),
    search: Optional[str] = Query(None)
):
    """List courses created by the current instructor"""
    try:
        courses = service.list_my_courses_service(
            user_id=current_user.id,
            limit=limit,
            offset=offset,
            search=search
        )
        return courses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching courses: {str(e)}")

@router.get("/{course_id}", response_model=CourseResponse)
async def get_course_api(
    course_id: str,
    current_user: AuthUser = Depends(get_current_user)
):
    """Get a specific course"""
    try:
        course = service.get_course_service(
            course_id=course_id,
            user_id=current_user.id
        )
        return course
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching course: {str(e)}")

@router.get("/", response_model=List[CourseResponse])
async def list_courses_api(
    current_user: AuthUser = Depends(auth_required),
    limit: Optional[int] = Query(100, ge=1, le=1000),
    offset: Optional[int] = Query(0, ge=0),
    search: Optional[str] = Query(None)
):
    """List courses the current user has joined"""
    try:
        courses = service.list_courses_service(
            user_id=current_user.id,
            limit=limit,
            offset=offset,
            search=search
        )
        return courses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching courses: {str(e)}")

@router.post("/join-by-code")
async def join_course_by_code(invite_code: str = Form(...), current_user: AuthUser = Depends(get_current_user)):
    """Join a course using a 6-digit invite code"""
    return service.join_course_by_invite_code_service(
        user_id=current_user.id,
        invite_code=invite_code
    )

@router.put("/{course_id}", response_model=CourseResponse)
async def update_course_api(
    course_id: str,
    course_data: CourseUpdate,
    current_user: AuthUser = Depends(instructor_required)
):
    """Update a course (only by the instructor who created it)"""
    return service.update_course_service(course_id, current_user.id, course_data)

@router.delete("/{course_id}")
async def delete_course_api(
    course_id: str,
    current_user: AuthUser = Depends(instructor_required)
):
    """Delete a course (only by the instructor who created it)"""
    try:
        # Check if course exists and user owns it
        course = get_course(course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        if course['created_by'] != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this course")
        
        # Delete course
        delete_course(course_id)
        return {"message": "Course deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting course: {str(e)}")



@router.get("/count/total")
async def get_course_count_api(current_user: AuthUser = Depends(get_current_user)):
    """Get course count for current user"""
    try:
        count = service.get_course_count_service(current_user.id)
        return count
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting course count: {str(e)}")
