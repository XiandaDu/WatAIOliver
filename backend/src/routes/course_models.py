from fastapi import APIRouter
from typing import List
from schemas.course_models import (
    CourseModelCreate,
    CourseModelDelete,
    CourseModelResponse,
)
from crud.course_models import (
    create_course_model,
    read_course_models,
    delete_course_model,
)

router = APIRouter(prefix="/course-models", tags=["course-models"])


@router.post("/", response_model=CourseModelResponse)
def api_create_course_model(entry: CourseModelCreate):
    return create_course_model(entry.course_id, entry.model_id)


@router.get("/{course_id}", response_model=List[CourseModelResponse])
def api_get_course_models(course_id: str):
    return read_course_models(course_id)


@router.delete("/", response_model=List[CourseModelResponse])
def api_delete_course_model(entry: CourseModelDelete):
    return delete_course_model(entry.course_id, entry.model_id)
