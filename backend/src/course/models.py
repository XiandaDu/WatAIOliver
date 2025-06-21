from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
from pydantic import BaseModel, Field
from typing import Optional

class Course(Base):
    __tablename__ = 't_course'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('t_user.id'))
    name = Column(String(200))
    notes = Column(String(2000))
    doc = Column(String(200))
    model = Column(String(200))
    prompt = Column(String(500))
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow)

    # relationships
    user = relationship("User", back_populates="courses")
    logs = relationship("Log", back_populates="course")

# Pydantic models for API
class CourseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Course name")
    notes: Optional[str] = Field(None, max_length=2000, description="Course notes")
    doc: Optional[str] = Field(None, max_length=200, description="Document path")
    model: Optional[str] = Field(None, max_length=200, description="AI model name")
    prompt: Optional[str] = Field(None, max_length=500, description="Course prompt")

class CourseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Course name")
    notes: Optional[str] = Field(None, max_length=2000, description="Course notes")
    doc: Optional[str] = Field(None, max_length=200, description="Document path")
    model: Optional[str] = Field(None, max_length=200, description="AI model name")
    prompt: Optional[str] = Field(None, max_length=500, description="Course prompt")

class CourseResponse(BaseModel):
    id: int
    user_id: int
    name: str
    notes: Optional[str]
    doc: Optional[str]
    model: Optional[str]
    prompt: Optional[str]
    create_time: datetime
    update_time: datetime

    class Config:
        from_attributes = True