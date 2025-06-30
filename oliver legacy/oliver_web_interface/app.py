import csv
import io
import os
import shutil
import uuid
from datetime import datetime
from chroma_utils import *
from evaluate_api import *
from fastapi import Depends, FastAPI, Request, UploadFile, File, Form, Query, HTTPException, status
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse, StreamingResponse
from starlette.templating import Jinja2Templates
from chromadb_utils import *
from models import User, Course, Log
from database import engine, get_db
from util.r import ok

from models import Base
from database import engine

from cachetools import TTLCache

# Initialize a TTL cache for storing session-based conversation state in memory.
# maxsize=100 means it can hold up to 100 sessions, ttl=3600 seconds (1 hour) expiration.

cache = TTLCache(maxsize=100, ttl=60 * 60)

# Create all database tables

Base.metadata.create_all(bind=engine)

import pymupdf4llm

# Initialize FastAPI application

templates = Jinja2Templates(directory="templates")
app = FastAPI(docs_url=None, redoc_url=None)

# Add session middleware to handle user sessions (e.g., login sessions)
app.add_middleware(SessionMiddleware, secret_key="your_secret_key",
                   max_age=3600)

# Mount static files and uploads directories for serving static content
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount('/uploads', StaticFiles(directory='uploads'), name='uploads')

import logging
from logging.handlers import RotatingFileHandler


def configure_logger():
    # Set up a rotating file logger to record application logs
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    log_file = 'app.log'

    handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024,
                                  backupCount=10)
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger


logger = configure_logger()

# Convert a PDF into markdown text using pymupdf4llm
def ingest_pdf(file_path, print_output=False):
    md_text = pymupdf4llm.to_markdown(file_path)
    if print_output:
        print(md_text)
    return md_text

# Retrieve the current user from session storage
def get_current_user(request: Request):
    user = request.session.get('session_user')
    if not user:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})
    return user


@app.post("/upload")
async def upload_file(request: Request, id: int = Form(...),
                      files: list[UploadFile] = File(...),
                      db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    collection_name = f"collection_{id}"
    collection = collection_new(collection_name)
    # Define allowed content types and extensions for uploaded files
    allowed_content_types = ['application/pdf', 'text/plain']
    allowed_extensions = ['pdf', 'txt', 'tex']

    file_list = []
    for file in files:
        content_type = file.content_type
        filename = file.filename
        file_extension = filename.split('.')[-1].lower()
        # Validate file type
        if content_type not in allowed_content_types and \
                file_extension not in allowed_extensions:
            continue

        file_path = 'uploads/' + filename
        # Save uploaded file to the server
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_list.append('/uploads/' + filename)

        text_content = ''
        # Extract text content from the file (PDF or text)
        if content_type == 'application/pdf' or file_extension == 'pdf':
            text_content = ingest_pdf(file_path, print_output=False)
        elif content_type == 'text/plain' or file_extension in ['txt', 'tex']:
            with open(file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()

        if text_content.strip():
            # Add the extracted content to ChromaDB for later retrieval
            add_to_chroma(text_content, filename, collection)
        else:
            raise ValueError("Text file is empty or invalid.")
    # Update the Course record in the database with the uploaded file paths
    db.query(Course).filter(Course.id == id).update(
        {"doc": ','.join(file_list)})
    db.commit()

    d = {"url": ','.join(file_list)}

    return ok(data=d)


@app.get("/")
def root():
    # Redirect the root path to the login page
    return RedirectResponse("/login")


@app.get("/login")
def login(request: Request):
    # Render the login template
    context = {}
    context['msg'] = request.session.pop("msg", None)
    return templates.TemplateResponse("login.html", {"request": request,
                                                     **context})


@app.post('/login')
def do_login(request: Request, username: str = Form(...),
             password: str = Form(...), db: Session = Depends(get_db)):
    # Authenticate user with provided username and password
    entity = db.query(User).filter(User.username == username,
                                   User.password == password).first()
    if not entity:
        request.session["msg"] = "Incorrect username or password"
        return RedirectResponse(url="/login", status_code=303)
    # Store user info in session
    request.session["session_user"] = {'id': entity.id,
                                       'name': entity.username,
                                       'nickname': entity.nickname}
    return RedirectResponse(url="/user_center", status_code=302)


@app.get("/logout")
def logout(request: Request):
    # Clear the session to log out the user
    request.session.clear()
    return RedirectResponse("/login")


@app.get("/user_center")
def user_center(request: Request, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    # Render user center page with user information
    context = {}
    context['user'] = db.query(User).filter(
        User.id == current_user['id']).first()

    return templates.TemplateResponse("user_center.html",
                                      {"request": request, **context})


@app.post('/user_info')
def user_info(request: Request, nickname: str = Form(...),
              db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    # Update the user's nickname and persist the change
    db.query(User).filter(User.id == current_user['id']) \
        .update({"nickname": nickname, "update_time": datetime.now()})
    db.commit()
    request.session["session_user"]['nickname'] = nickname
    return RedirectResponse(url="/user_center", status_code=302)


def build_conversation_history(conversation, max_tokens=1024):
    # Reconstruct conversation history from the end, ensuring token count does not exceed max_tokens
    conversation_history = ""
    total_tokens = 0
    for turn in reversed(conversation):
        user_turn = f"User: {turn['question']}\n"
        assistant_turn = f"Assistant: {turn.get('answer', '')}\n"
        turn_text = user_turn + assistant_turn
        turn_tokens = len(turn_text.split())
        if total_tokens + turn_tokens <= max_tokens:
            conversation_history = turn_text + conversation_history
            total_tokens += turn_tokens
        else:
            break
    return conversation_history


def get_background_text(background_chunks, max_background_tokens):
    # Concatenate background chunks up to a maximum token limit
    background_text = ""
    total_tokens = 0
    for chunk in background_chunks:
        chunk_tokens = len(tokenizer.tokenize(chunk))
        if total_tokens + chunk_tokens <= max_background_tokens:
            background_text += chunk + "\n"
            total_tokens += chunk_tokens
        else:
            break
    return background_text


def summarize_interaction(conversation, max_tokens=150):
    # Summarize the last user-assistant exchange.
    last_exchange = f"User: {conversation[-1]['question']}\nAssistant: {conversation[-1]['answer']}\n"

    previous_summary = conversation[-2]['summary'] if len(conversation) > 1 and 'summary' in conversation[-2] else ''

    summary_prompt = f"Previous Summary:\n{previous_summary}\n\nNew Interaction:\n{last_exchange}\n\nUpdate the summary, keeping it under {max_tokens} tokens."

    # Generate a summary of the updated conversation
    summary = text_text_eval(document_text="", prompt_text=summary_prompt, model="phi", max_length=max_tokens)
    return summary.strip()


# Reset the conversation stored in the session
@app.get("/reset_conversation")
def reset_conversation(request: Request, link: str = Query(default=''), current_user: dict = Depends(get_current_user)):
    request.session['conversation'] = []
    print(link)
    if len(link) == 0:
        return RedirectResponse(url="/open", status_code=302)
    else:
        return RedirectResponse(url="/open/" + link, status_code=302)

# Render an open Q&A interface without specifying a course
@app.get("/open")
def open_all(request: Request, db: Session = Depends(get_db)):
    context = {}
    context['user_list'] = db.query(User).all()
    context['link'] = ''
    request.session["session_id"] = str(uuid.uuid4())
    return templates.TemplateResponse("open.html", {"request": request,
                                                    **context})

# Render an open Q&A interface for a specific course identified by 'link'
@app.get("/open/{link}")
def open_link(request: Request, link: str, db: Session = Depends(get_db)):
    context = {}
    context['link'] = link
    request.session["session_id"] = str(uuid.uuid4())
    return templates.TemplateResponse("open.html", {"request": request,
                                                    **context})


@app.post("/open_ask")
async def open_ask(request: Request, link: str = Form(default=''),
                   question: str = Form(...), db: Session = Depends(get_db)):
    course_id = -1
    model_name = 'phi'
    system_prompt = None
    # If a link is provided, try to match it to a course and retrieve its settings
    if link is not None and len(link) > 0:
        course = db.query(Course).filter(Course.name == link).first()
        if course is not None:
            course_id = course.id
            model_name = course.model
            system_prompt = course.prompt

    logger.info("Course ID: %s, Question: %s", course_id, question)

    session_id = request.session.get("session_id")
    conversation = []
    print(session_id)
    if session_id in cache:
        conversation = cache.get(session_id)
    # conversation = request.session.get('conversation', [])
    logger.info(conversation)

    # conversation.append({'question': question})
    this_conversation = {'question': question}
    # Limit the stored conversation length to prevent overly long context
    MAX_CONVERSATION_LENGTH = 10
    if len(conversation) > MAX_CONVERSATION_LENGTH:
        conversation = conversation[-MAX_CONVERSATION_LENGTH:]

    SIMILARITY_THRESHOLD = 0.5
    MAX_BACKGROUND_TOKENS = 500

    background_query = "No documents uploaded, please provide background information."
    background_summary = ""
    summary = ""
    # If course_id is valid, attempt to retrieve relevant context from ChromaDB
    if course_id != -1:
        collection_name = f"collection_{course_id}"
        collection = collection_exists(collection_name)
        if collection is not None:

            top_results_query = query_sentence_with_threshold(collection, question, 5, SIMILARITY_THRESHOLD)
            background_query = get_background_text(top_results_query, MAX_BACKGROUND_TOKENS)
            print(f"Background Query:\n{background_query}")

            if len(conversation) >= 1 and 'summary' in conversation[-1]:
                summary = conversation[-1]['summary']
                top_results_summary = query_sentence_with_threshold(collection, summary, 5, SIMILARITY_THRESHOLD)
                background_summary = get_background_text(top_results_summary, MAX_BACKGROUND_TOKENS)
                print(f"Background Summary:\n{background_summary}")

    this_conversation['background'] = background_query + "\n" + background_summary

    MAX_TOKENS = 1024
    # Use a default system prompt if none is configured
    if not system_prompt:
        system_prompt = ("Respond to the question using information in the "
                         "background. If no relevant information exists in the "
                         "background, you must say so and then refuse to "
                         "answer further.")

    logger.info(question)
    logger.info(system_prompt)
    logger.info(background_query)
    logger.info(summary)
    logger.info('')
    # Construct the final prompt including user query, background, and conversation summar
    final_prompt = (
        f"You are a helpful teaching assistant.\n{system_prompt}\n\n"
        f"User Query:\n{question}\n\n"
        f"Based on this query, here is some background information that may be relevant (it may not be):\n{background_query}\n\n"
        f"This query is part of a longer conversation. Here is a brief summary:\n{summary}\n\n"
        f"Based on the summary, here is some additional background information that may be relevant (it may not be):\n{background_summary}\n\n"
        f"Please provide a response to the user's query."
    )

    # Generate an answer using the specified LLM
    answer = text_text_eval(document_text=final_prompt, prompt_text=question, model=model, max_length=1024)

    this_conversation['answer'] = answer
    # Add the current Q&A to the conversation and update the summary
    conversation.append(this_conversation)
    new_summary = summarize_interaction(conversation)
    conversation[-1]['summary'] = new_summary

    logger.info(conversation)
    # Store the updated conversation in cache
    cache[session_id] = conversation
    # Log the interaction to the database
    entity = Log()
    entity.create_time = datetime.now()
    entity.background = background_query + "\n" + background_summary
    entity.query = question
    entity.answer = answer
    entity.llm = answer
    entity.link = link
    entity.course_id = course_id
    db.add(entity)
    db.commit()

    return {"answer": answer}

# Reset the conversation for the open Q&A session
@app.get("/reset_conversation_open")
def reset_conversation_open(request: Request):
    request.session['conversation'] = []
    return RedirectResponse(url="/open", status_code=302)

# Display a list of courses owned by the current user
@app.get("/course")
def course(request: Request, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    context = {}
    context['rows'] = db.query(Course).filter(Course.user_id == current_user['id']).all()

    return templates.TemplateResponse("course.html", {"request": request, **context})


@app.get("/course/add")
# Render a form to add a new course
def course_add(request: Request, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    context = {}
    context['row'] = {'id': -1}
    return templates.TemplateResponse("course_form.html", {"request": request, **context})


@app.get("/course/edit")
# Render a form to edit an existing course
def course_edit(request: Request, id: int = Query(...), db: Session = Depends(get_db),
                current_user: dict = Depends(get_current_user)):
    context = {}
    context['row'] = db.query(Course).filter(Course.id == id).first()
    return templates.TemplateResponse("course_form.html", {"request": request, **context})


@app.post("/course/save")
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

    return RedirectResponse(url="/course", status_code=302)


@app.get("/course/upload")
def pdf(request: Request, id: int = Query(...), db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)):
    # Render the file upload form for a specific course
    context = {}
    context['row'] = db.query(Course).filter(Course.id == id).first()
    return templates.TemplateResponse("pdf.html", {"request": request, **context})


@app.get("/course/delete")
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
    try:
        client.delete_collection(name=collection_name)
        print(f"ChromaDB collection '{collection_name}' deleted successfully.")
    except Exception as e:
        print(f"Error deleting ChromaDB collection '{collection_name}': {e}")

    return RedirectResponse(url="/course", status_code=302)


@app.get("/course/remove_docs")
def course_remove_docs(request: Request, id: int = Query(...), db: Session = Depends(get_db),
                       current_user: dict = Depends(get_current_user)):
    # Remove all documents associated with a course from ChromaDB and the DB record
    collection_name = f"collection_{id}"
    collection_remove(collection_name)
    db.query(Course).filter(Course.id == id).update(
        {"doc": ''})
    db.commit()
    return RedirectResponse(url="/course", status_code=302)

# Export conversation logs for a given course as a CSV file
@app.get("/course/export")
async def export_data(id: int = Query(...), db: Session = Depends(get_db)):
    rows = db.query(Log).filter(Log.course_id == id).all()
    data = []
    for i in rows:
        if i:
            d = i.__dict__
            d.pop('_sa_instance_state')
            d.pop('id')
            d.pop('user_id')
            d.pop('answer')
            data.append(d)
            print(d)

    file_like = io.StringIO()
    writer = csv.DictWriter(file_like, fieldnames=["course_id", "query", "background", "llm", "link", "create_time"])
    writer.writeheader()
    writer.writerows(data)

    response = StreamingResponse(iter([file_like.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=log.csv"
    return response
