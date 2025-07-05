from fastapi import APIRouter, Request, Depends, HTTPException, Query, status, Form
from . import service
# from .CRUD import (
#     create_course, get_course, get_courses_by_user, get_all_courses,
#     update_course, delete_course, search_courses, get_course_count
# )
from .CRUD import (
    create_course, 
    update_course, delete_course
)
from .models import CourseCreate, CourseUpdate, CourseResponse
from typing import List, Optional

import csv
import io
import os
from sqlalchemy.orm import Session
from .database import engine, get_db
from .models import Course
from datetime import datetime
from starlette.responses import RedirectResponse, StreamingResponse
from .service import get_current_user

router = APIRouter(
    prefix='/course',
    tags=['course']
)

# REST API Endpoints using Supabase

@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course_api(
    course_data: CourseCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new course"""
    try:
        course = create_course(
            user_id=current_user['id'],
            name=course_data.name,
            notes=course_data.notes,
            doc=course_data.doc,
            model=course_data.model,
            prompt=course_data.prompt
        )
        if not course:
            raise HTTPException(status_code=400, detail="Failed to create course")
        return CourseResponse(**course)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating course: {str(e)}")

@router.get("/{course_id}", response_model=CourseResponse)
async def get_course_api(
    course_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific course by ID"""
    course = get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if user owns this course
    if course['user_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return CourseResponse(**course)

@router.get("/", response_model=List[CourseResponse])
async def list_courses_api(
    current_user: dict = Depends(get_current_user),
    limit: Optional[int] = Query(100, ge=1, le=1000),
    offset: Optional[int] = Query(0, ge=0),
    search: Optional[str] = Query(None)
):
    """Get all courses for the current user"""
    try:
        if search:
            courses = search_courses(current_user['id'], search)
        else:
            courses = get_courses_by_user(current_user['id'])
        
        # Apply pagination
        if offset:
            courses = courses[offset:]
        if limit:
            courses = courses[:limit]
        
        return [CourseResponse(**course) for course in courses]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching courses: {str(e)}")

@router.put("/{course_id}", response_model=CourseResponse)
async def update_course_api(
    course_id: int,
    course_data: CourseUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a course"""
    # First check if course exists and user owns it
    existing_course = get_course(course_id)
    if not existing_course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if existing_course['user_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Only update provided fields
        update_data = course_data.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        updated_course = update_course(course_id, **update_data)
        if not updated_course:
            raise HTTPException(status_code=400, detail="Failed to update course")
        
        return CourseResponse(**updated_course)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating course: {str(e)}")

@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course_api(
    course_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete a course"""
    # First check if course exists and user owns it
    existing_course = get_course(course_id)
    if not existing_course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if existing_course['user_id'] != current_user['id']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        success = delete_course(course_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to delete course")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting course: {str(e)}")

@router.get("/count/total")
async def get_course_count_api(current_user: dict = Depends(get_current_user)):
    """Get total course count for the current user"""
    try:
        count = get_course_count(current_user['id'])
        return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting course count: {str(e)}")

# Legacy endpoints for backward compatibility (keeping existing functionality)

@router.get("/add")
def course_add(request: Request, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Render a form to add a new course"""
    context = {}
    context['row'] = {'id': -1}
    return "add"

@router.get("/edit")
def course_edit(request: Request, id: int = Query(...), db: Session = Depends(get_db),
                current_user: dict = Depends(get_current_user)):
    """Render a form to edit an existing course"""
    context = {}
    context['row'] = db.query(Course).filter(Course.id == id).first()
    return "edit"

@router.post("/save")
def course_save(request: Request, id: int = Form(...), name: str = Form(...), notes: str = Form(None),
                model: str = Form(None), prompt: str = Form(None),
                db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Save or update course information in the database"""
    print(id, name, notes)
    # Save or update course information in the database
    if id > 0:
        db.query(Course).filter(Course.id == id).update(
            {"name": name, "update_time": datetime.now(), 'notes': notes, 'model': model, 'prompt': prompt})
        db.commit()
    else:
        entity = Course()
        entity.create_time = datetime.now()
        entity.update_time = datetime.now()
        entity.user_id = current_user['id']
        entity.name = name
        entity.notes = notes
        entity.model = model
        entity.prompt = prompt
        db.add(entity)
        db.commit()

    return RedirectResponse(url="/", status_code=302)

@router.get("/upload")
def pdf(request: Request, id: int = Query(...), db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)):
    """Render the file upload form for a specific course"""
    context = {}
    context['row'] = db.query(Course).filter(Course.id == id).first()
    return "upload"

@router.get("/delete")
def course_delete(request: Request, id: int = Query(...), db: Session = Depends(get_db),
                  current_user: dict = Depends(get_current_user)):
    """Delete a course and its associated documents"""
    course = db.query(Course).filter(Course.id == id).first()
    if course and course.doc:
        file_paths = course.doc.split(',')
        for file_path in file_paths:
            file_path = file_path.lstrip('/')
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"File '{file_path}' deleted successfully.")
            else:
                print(f"File '{file_path}' does not exist.")

    db.query(Course).filter(Course.id == id).delete()
    db.commit()

    collection_name = f"collection_{id}"
    # try:
    #     client.delete_collection(name=collection_name)
    #     print(f"ChromaDB collection '{collection_name}' deleted successfully.")
    # except Exception as e:
    #     print(f"Error deleting ChromaDB collection '{collection_name}': {e}")

    return RedirectResponse(url="/", status_code=302)

@router.get("/remove_docs")
def course_remove_docs(request: Request, id: int = Query(...), db: Session = Depends(get_db),
                       current_user: dict = Depends(get_current_user)):
    """Remove all documents associated with a course"""
    # # Remove all documents associated with a course from ChromaDB and the DB record
    # collection_name = f"collection_{id}"
    # collection_remove(collection_name)
    # db.query(Course).filter(Course.id == id).update(
    #     {"doc": ''})
    # db.commit()
    return RedirectResponse(url="/course", status_code=302)

@router.get("/export")
async def export_data(id: int = Query(...), db: Session = Depends(get_db)):
    """Export conversation logs for a given course as a CSV file"""
    # rows = db.query(Log).filter(Log.course_id == id).all()
    # data = []
    # for i in rows:
    #     if i:
    #         d = i.__dict__
    #         d.pop('_sa_instance_state')
    #         d.pop('id')
    #         d.pop('user_id')
    #         d.pop('answer')
    #         data.append(d)
    #         print(d)

    # file_like = io.StringIO()
    # writer = csv.DictWriter(file_like, fieldnames=["course_id", "query", "background", "llm", "link", "create_time"])
    # writer.writeheader()
    # writer.writerows(data)

    # response = StreamingResponse(iter([file_like.getvalue()]), media_type="text/csv")
    # response.headers["Content-Disposition"] = "attachment; filename=log.csv"
    # return response
    return "export"
