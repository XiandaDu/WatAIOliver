from fastapi import APIRouter, Request, Depends, Form, Query
from . import service

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

# Display a list of courses owned by the current user
@router.get("/")
def course(request: Request, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return "root"


@router.get("/add")
# Render a form to add a new course
def course_add(request: Request, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    context = {}
    context['row'] = {'id': -1}
    return "add"


@router.get("/edit")
# Render a form to edit an existing course
def course_edit(request: Request, id: int = Query(...), db: Session = Depends(get_db),
                current_user: dict = Depends(get_current_user)):
    context = {}
    context['row'] = db.query(Course).filter(Course.id == id).first()
    return "edit"


@router.post("/save")
def course_save(request: Request, id: int = Form(...), name: str = Form(...), notes: str = Form(None),
                model: str = Form(None), prompt: str = Form(None),
                db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
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
    # Render the file upload form for a specific course
    context = {}
    context['row'] = db.query(Course).filter(Course.id == id).first()
    return "upload"


@router.get("/delete")
def course_delete(request: Request, id: int = Query(...), db: Session = Depends(get_db),
                  current_user: dict = Depends(get_current_user)):
    # Delete a course and its associated documents from the server and ChromaDB
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
    # # Remove all documents associated with a course from ChromaDB and the DB record
    # collection_name = f"collection_{id}"
    # collection_remove(collection_name)
    # db.query(Course).filter(Course.id == id).update(
    #     {"doc": ''})
    # db.commit()
    return RedirectResponse(url="/course", status_code=302)

# Export conversation logs for a given course as a CSV file
@router.get("/export")
async def export_data(id: int = Query(...), db: Session = Depends(get_db)):
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
