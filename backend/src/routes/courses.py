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
from typing import List, Optional
from sqlalchemy.orm import Session

router = APIRouter(prefix="/course", tags=["course"])
