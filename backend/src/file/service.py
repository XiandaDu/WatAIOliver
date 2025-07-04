from fastapi import Depends, FastAPI, Request, UploadFile, File, Form, Query, HTTPException, status
from .models import FileUpload, FileCreate, FileUpdate, FileResponse, FileListResponse
# from .CRUD import (
#     create_file, get_file, get_files_by_user, get_files_by_course, get_all_files,
#     update_file, delete_file, search_files, get_file_count, get_file_count_by_course,
#     get_files_by_type, get_files_by_size_range
# )
from .CRUD import (
    create_file,
    update_file, delete_file
)
from typing import List, Optional, Dict, Any
import pymupdf4llm
import shutil
import os

def upload_file(data: FileUpload):
    # collection_name = f"collection_{id}"
    # collection = collection_new(collection_name)
    # # Define allowed content types and extensions for uploaded files
    # allowed_content_types = ['application/pdf', 'text/plain']
    # allowed_extensions = ['pdf', 'txt', 'tex']

    # file_list = []
    # for file in files:
    #     content_type = file.content_type
    #     filename = file.filename
    #     file_extension = filename.split('.')[-1].lower()
    #     # Validate file type
    #     if content_type not in allowed_content_types and \
    #             file_extension not in allowed_extensions:
    #         continue

    #     file_path = 'uploads/' + filename
    #     # Save uploaded file to the server
    #     with open(file_path, "wb") as buffer:
    #         shutil.copyfileobj(file.file, buffer)

    #     file_list.append('/uploads/' + filename)

    #     text_content = ''
    #     # Extract text content from the file (PDF or text)
    #     if content_type == 'application/pdf' or file_extension == 'pdf':
    #         text_content = ingest_pdf(file_path, print_output=False)
    #     elif content_type == 'text/plain' or file_extension in ['txt', 'tex']:
    #         with open(file_path, 'r', encoding='utf-8') as f:
    #             text_content = f.read()

    #     if text_content.strip():
    #         # Add the extracted content to ChromaDB for later retrieval
    #         add_to_chroma(text_content, filename, collection)
    #     else:
    #         raise ValueError("Text file is empty or invalid.")
    # # Update the Course record in the database with the uploaded file paths
    # db.query(Course).filter(Course.id == id).update(
    #     {"doc": ','.join(file_list)})
    # db.commit()

    # d = {"url": ','.join(file_list)}

    # return ok(data=d)
    pass

def ingest_pdf(file_path, print_output=False):
    md_text = pymupdf4llm.to_markdown(file_path)
    if print_output:
        print(md_text)
    return md_text

# Business logic functions using Supabase CRUD

def create_file_service(user_id: str, file_data: FileCreate) -> FileResponse:
    """Create a new file record with business logic validation"""
    try:
        # Validate file path exists
        if not os.path.exists(file_data.file_path):
            raise HTTPException(status_code=400, detail="File path does not exist")
        
        file = create_file(
            user_id=user_id,
            file_name=file_data.file_name,
            file_type=file_data.file_type,
            file_size=file_data.file_size,
            file_path=file_data.file_path,
            description=file_data.description,
            course_id=file_data.course_id
        )
        if not file:
            raise HTTPException(status_code=400, detail="Failed to create file record")
        return FileResponse(**file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating file record: {str(e)}")

def get_file_service(file_id: int, user_id: str) -> FileResponse:
    """Get a file with ownership validation"""
    file = get_file(file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if file['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return FileResponse(**file)

def list_files_service(user_id: str, limit: Optional[int] = None, 
                      offset: Optional[int] = None, search: Optional[str] = None,
                      course_id: Optional[int] = None, file_type: Optional[str] = None) -> FileListResponse:
    """Get files for a user with optional filtering and pagination"""
    try:
        if course_id:
            files = get_files_by_course(course_id)
        elif file_type:
            files = get_files_by_type(user_id, file_type)
        elif search:
            files = search_files(user_id, search)
        else:
            files = get_files_by_user(user_id)
        
        total = len(files)
        
        # Apply pagination
        if offset:
            files = files[offset:]
        if limit:
            files = files[:limit]
        
        per_page = limit or total
        page = (offset or 0) // (limit or 1) + 1 if limit else 1
        total_pages = (total + per_page - 1) // per_page if per_page > 0 else 1
        
        return FileListResponse(
            files=[FileResponse(**file) for file in files],
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching files: {str(e)}")

def update_file_service(file_id: int, user_id: str, file_data: FileUpdate) -> FileResponse:
    """Update a file with ownership validation"""
    # Check ownership first
    existing_file = get_file(file_id)
    if not existing_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if existing_file['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        update_data = file_data.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        updated_file = update_file(file_id, **update_data)
        if not updated_file:
            raise HTTPException(status_code=400, detail="Failed to update file")
        
        return FileResponse(**updated_file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating file: {str(e)}")

def delete_file_service(file_id: int, user_id: str) -> bool:
    """Delete a file with ownership validation and physical file cleanup"""
    # Check ownership first
    existing_file = get_file(file_id)
    if not existing_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if existing_file['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Delete physical file if it exists
        file_path = existing_file['file_path']
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete database record
        success = delete_file(file_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to delete file record")
        return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

def get_file_count_service(user_id: str) -> Dict[str, int]:
    """Get file count for a user"""
    try:
        count = get_file_count(user_id)
        return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting file count: {str(e)}")

def get_file_count_by_course_service(course_id: int) -> Dict[str, int]:
    """Get file count for a course"""
    try:
        count = get_file_count_by_course(course_id)
        return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting file count: {str(e)}")

def get_files_by_size_range_service(user_id: str, min_size: Optional[int] = None, 
                                   max_size: Optional[int] = None) -> List[FileResponse]:
    """Get files within a size range for a user"""
    try:
        files = get_files_by_size_range(user_id, min_size, max_size)
        return [FileResponse(**file) for file in files]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching files by size: {str(e)}")
