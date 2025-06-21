from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime

class FileBase(BaseModel):
    user_id: str
    file_name: str
    file_type: str
    file_size: int
    file_path: str

# Pydantic models for API operations
class FileCreate(BaseModel):
    user_id: str = Field(..., description="User ID who owns the file")
    file_name: str = Field(..., min_length=1, max_length=255, description="Name of the file")
    file_type: str = Field(..., min_length=1, max_length=50, description="Type/extension of the file")
    file_size: int = Field(..., gt=0, description="Size of the file in bytes")
    file_path: str = Field(..., min_length=1, max_length=500, description="Path to the file on server")
    description: Optional[str] = Field(None, max_length=1000, description="Optional description of the file")
    course_id: Optional[int] = Field(None, description="Associated course ID if applicable")

class FileUpdate(BaseModel):
    file_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Name of the file")
    description: Optional[str] = Field(None, max_length=1000, description="Description of the file")
    course_id: Optional[int] = Field(None, description="Associated course ID")

class FileResponse(BaseModel):
    id: int
    user_id: str
    file_name: str
    file_type: str
    file_size: int
    file_path: str
    description: Optional[str]
    course_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class FileUpload(BaseModel):
    """Model for file upload requests"""
    course_id: Optional[int] = Field(None, description="Course ID to associate the file with")
    description: Optional[str] = Field(None, max_length=1000, description="File description")

class FileListResponse(BaseModel):
    """Response model for file listing with pagination"""
    files: list[FileResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
