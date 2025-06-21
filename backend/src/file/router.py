from fastapi import APIRouter, Request, Depends, HTTPException, Query, status, UploadFile, File, Form
from . import service
from .models import FileUpload, FileCreate, FileUpdate, FileResponse, FileListResponse
from .service import (
    create_file_service, get_file_service, list_files_service, update_file_service,
    delete_file_service, get_file_count_service, get_file_count_by_course_service,
    get_files_by_size_range_service, upload_file
)
from typing import List, Optional
import os
import shutil
from datetime import datetime

router = APIRouter(
    prefix='/file',
    tags=['file']
)

# REST API Endpoints using Supabase

@router.post("/", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def create_file_api(
    file_data: FileCreate,
    current_user: dict = Depends(service.get_current_user)
):
    """Create a new file record"""
    return create_file_service(current_user['id'], file_data)

@router.get("/{file_id}", response_model=FileResponse)
async def get_file_api(
    file_id: int,
    current_user: dict = Depends(service.get_current_user)
):
    """Get a specific file by ID"""
    return get_file_service(file_id, current_user['id'])

@router.get("/", response_model=FileListResponse)
async def list_files_api(
    current_user: dict = Depends(service.get_current_user),
    limit: Optional[int] = Query(100, ge=1, le=1000),
    offset: Optional[int] = Query(0, ge=0),
    search: Optional[str] = Query(None),
    course_id: Optional[int] = Query(None),
    file_type: Optional[str] = Query(None)
):
    """Get all files for the current user with optional filtering"""
    return list_files_service(
        user_id=current_user['id'],
        limit=limit,
        offset=offset,
        search=search,
        course_id=course_id,
        file_type=file_type
    )

@router.put("/{file_id}", response_model=FileResponse)
async def update_file_api(
    file_id: int,
    file_data: FileUpdate,
    current_user: dict = Depends(service.get_current_user)
):
    """Update a file"""
    return update_file_service(file_id, current_user['id'], file_data)

@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file_api(
    file_id: int,
    current_user: dict = Depends(service.get_current_user)
):
    """Delete a file"""
    delete_file_service(file_id, current_user['id'])

@router.get("/count/total")
async def get_file_count_api(current_user: dict = Depends(service.get_current_user)):
    """Get total file count for the current user"""
    return get_file_count_service(current_user['id'])

@router.get("/count/course/{course_id}")
async def get_file_count_by_course_api(course_id: int):
    """Get file count for a specific course"""
    return get_file_count_by_course_service(course_id)

@router.get("/size/range")
async def get_files_by_size_range_api(
    current_user: dict = Depends(service.get_current_user),
    min_size: Optional[int] = Query(None, ge=0),
    max_size: Optional[int] = Query(None, ge=0)
):
    """Get files within a size range for the current user"""
    return get_files_by_size_range_service(current_user['id'], min_size, max_size)

# File upload endpoint (enhanced version)
@router.post("/upload", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file_api(
    file: UploadFile = File(...),
    course_id: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    current_user: dict = Depends(service.get_current_user)
):
    """Upload a file and create a file record"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Create uploads directory if it doesn't exist
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        unique_filename = f"{current_user['id']}_{int(datetime.utcnow().timestamp())}_{file.filename}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Create file record
        file_data = FileCreate(
            user_id=current_user['id'],
            file_name=file.filename,
            file_type=file_extension,
            file_size=file_size,
            file_path=file_path,
            description=description,
            course_id=course_id
        )
        
        return create_file_service(current_user['id'], file_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

# Legacy endpoint for backward compatibility
@router.post("/upload/legacy")
async def upload_file_legacy(data: FileUpload):
    """Legacy file upload endpoint"""
    return upload_file(data)

# Additional utility endpoints

@router.get("/course/{course_id}", response_model=List[FileResponse])
async def get_files_by_course_api(
    course_id: int,
    current_user: dict = Depends(service.get_current_user)
):
    """Get all files for a specific course"""
    from .CRUD import get_files_by_course
    files = get_files_by_course(course_id)
    return [FileResponse(**file) for file in files]

@router.get("/type/{file_type}", response_model=List[FileResponse])
async def get_files_by_type_api(
    file_type: str,
    current_user: dict = Depends(service.get_current_user)
):
    """Get all files of a specific type for the current user"""
    from .CRUD import get_files_by_type
    files = get_files_by_type(current_user['id'], file_type)
    return [FileResponse(**file) for file in files]