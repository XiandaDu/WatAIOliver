from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DocumentCreate(BaseModel):
    document_id: str
    course_id: Optional[str] = None
    term: Optional[str] = None
    title: str
    content: str

class DocumentUpdate(BaseModel):
    course_id: Optional[str] = None
    term: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None

class DocumentResponse(BaseModel):
    document_id: str
    course_id: Optional[str]
    term: Optional[str]
    title: str
    content: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]