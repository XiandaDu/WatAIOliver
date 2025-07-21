from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class CourseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Course title")
    description: Optional[str] = Field(None, description="Course description")
    term: Optional[str] = Field(None, max_length=200, description="Academic term")
    created_by: Optional[str] = Field(
        None, max_length=200, description="Created by user"
    )


class CourseUpdate(BaseModel):
    title: Optional[str] = Field(
        None, min_length=1, max_length=200, description="Course title"
    )
    description: Optional[str] = Field(None, description="Course description")
    term: Optional[str] = Field(None, max_length=200, description="Academic term")
    created_by: Optional[str] = Field(
        None, max_length=200, description="Created by user"
    )


class CourseResponse(BaseModel):
    course_id: str
    title: str
    description: Optional[str]
    term: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
