from fastapi import APIRouter, Request, Depends, HTTPException, Query, status, Form
from . import service
from .CRUD import (
    create_course, get_course, get_courses, get_all_courses,
    search_courses, get_course_count, update_course, delete_course
)
from .models import CourseCreate, CourseUpdate, CourseResponse
from typing import List, Optional

import csv
import io
import os
from sqlalchemy.orm import Session
from .database import engine, get_db
from .models import Course
from datetime import datetime
from starlette.responses import RedirectResponse, StreamingResponse
from src.auth.middleware import auth_required, get_current_user
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
    current_user = Depends(auth_required),
    limit: Optional[int] = Query(100, ge=1, le=1000),
    offset: Optional[int] = Query(0, ge=0),
    search: Optional[str] = Query(None)
):
    """List all courses for the current user"""
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
    current_user: AuthUser = Depends(get_current_user)
):
    """Update a course"""
    try:
        course = service.update_course_service(
            course_id=course_id,
            user_id=current_user.id,
            course_data=course_data
        )
        return course
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating course: {str(e)}")

@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course_api(
    course_id: str,
    current_user: AuthUser = Depends(get_current_user)
):
    """Delete a course"""
    try:
        success = service.delete_course_service(
            course_id=course_id,
            user_id=current_user.id
        )
        return None
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

# Legacy endpoints - keeping for compatibility but may need updates
@router.get("/add")
def course_add(request: Request, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return {"message": "Legacy endpoint - use POST / instead"}

@router.get("/edit")
def course_edit(request: Request, id: str = Query(...), db: Session = Depends(get_db),
                current_user: dict = Depends(get_current_user)):
    return {"message": "Legacy endpoint - use PUT /{course_id} instead"}

@router.post("/save")
def course_save(request: Request, id: str = Form(...), title: str = Form(...), description: str = Form(None),
                term: str = Form(None), 
                db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return {"message": "Legacy endpoint - use PUT /{course_id} instead"}

@router.get("/upload")
def pdf(request: Request, id: str = Query(...), db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)):
    return {"message": "Legacy endpoint - use file upload endpoints instead"}

@router.get("/delete")
def course_delete(request: Request, id: str = Query(...), db: Session = Depends(get_db),
                  current_user: dict = Depends(get_current_user)):
    return {"message": "Legacy endpoint - use DELETE /{course_id} instead"}

@router.get("/remove_docs")
def course_remove_docs(request: Request, id: str = Query(...), db: Session = Depends(get_db),
                       current_user: dict = Depends(get_current_user)):
    return {"message": "Legacy endpoint"}

@router.get("/export")
async def export_data(id: str = Query(...), db: Session = Depends(get_db)):
    return {"message": "Legacy endpoint"}
