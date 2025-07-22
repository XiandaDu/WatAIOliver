from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
from pydantic import BaseModel, Field
from typing import Optional

class Course(Base):
    __tablename__ = 'courses'

    course_id = Column(String, primary_key=True, index=True)
    title = Column(String(200))
    description = Column(Text)
    term = Column(String(200))
    created_by = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # relationships - commented out since schema changed
    # user = relationship("User", back_populates="courses")
    # logs = relationship("Log", back_populates="course")

# Pydantic models for API
class CourseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Course title")
    description: Optional[str] = Field(None, description="Course description")
    term: Optional[str] = Field(None, max_length=200, description="Academic term")
    created_by: Optional[str] = Field(None, max_length=200, description="Created by user")

class CourseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Course title")
    description: Optional[str] = Field(None, description="Course description")
    term: Optional[str] = Field(None, max_length=200, description="Academic term")
    created_by: Optional[str] = Field(None, max_length=200, description="Created by user")

class CourseResponse(BaseModel):
    course_id: str
    title: str
    description: Optional[str]
    term: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True