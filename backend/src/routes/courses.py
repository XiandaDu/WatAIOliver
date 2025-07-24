from fastapi import APIRouter, Request, Depends, HTTPException, Query, status, Form
from crud.courses import (
    create_course,
    get_course,
    get_courses,
    get_course_count,
    update_course,
    delete_course,
)
from schemas.courses import CourseCreate, CourseUpdate, CourseResponse
from typing import List

router = APIRouter(prefix="/course", tags=["course"])


@router.post("/", response_model=CourseResponse)
def api_create_course(course: CourseCreate):
    return create_course(course)


@router.get("/{user_id}", response_model=List[CourseResponse])
def api_get_courses(user_id: str):
    return get_courses(user_id)


@router.put("/{course_id}", response_model=CourseResponse)
def api_update_course(course_id: str, update: CourseUpdate):
    return update_course(course_id, update)


@router.delete("/{course_id}")
def api_delete_course(course_id: str):
    return delete_course(course_id)
