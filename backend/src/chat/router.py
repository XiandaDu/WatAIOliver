from fastapi import APIRouter, Request, UploadFile, File, Form, Query, HTTPException, status

from typing import List
import tempfile
import os
import httpx

from backend.constants import TimeoutConfig, ServiceConfig

from . import service
from .models import ConversationCreate, ConversationUpdate, ConversationDelete, MessageCreate, MessageUpdate, MessageDelete, ConversationOut, MessageOut, ChatRequest
from . import CRUD as supabase_crud

router = APIRouter(
    prefix='/chat',
    tags=['chat']
)


@router.post("/")
async def chat(data: ChatRequest):
    return await service.generate_response(data)

@router.post("")
async def chat_root(data: ChatRequest):
    return await service.generate_response(data)

@router.post("/open_ask")
async def open_ask(data: ConversationCreate):
    return service.open_ask(data)

@router.post("/create_conversation")
async def create_conversation(data: ConversationCreate, response_model=ConversationOut):
    result = supabase_crud.create_conversation(data)
    return result

@router.get("/conversations/{user_id}")
async def get_conversations(user_id: str, response_model=ConversationOut):
    result = supabase_crud.get_conversations(user_id)
    return result

@router.post("/update_conversation")
async def update_conversation(data: ConversationUpdate, response_model=ConversationOut):
    result = supabase_crud.update_conversation(data)
    return result

@router.post("/delete_conversation")
async def delete_conversation(data: ConversationDelete, response_model=ConversationOut):
    result = supabase_crud.delete_conversation(data)
    return result

@router.post("/create_message")
async def create_message(data: MessageCreate, response_model=MessageOut):
    result = supabase_crud.create_message(data)
    return result

@router.get("/messages/{conversation_id}")
async def get_messages(conversation_id: str, response_model=MessageOut):
    result = supabase_crud.get_messages(conversation_id)
    return result

@router.post("/update_message")
async def update_message(data: MessageUpdate, response_model=MessageOut):
    return supabase_crud.update_message(data)

@router.post("/delete_message")
async def delete_message(data: MessageDelete, response_model=MessageOut):
    return supabase_crud.delete_message(data)

@router.post("/upload_files")
async def upload_files(
    files: List[UploadFile] = File(...),
    conversation_id: str = Form(...),
    user_id: str = Form(...)
):
    try:
        results = await service.process_files_for_chat(files, conversation_id, user_id)
        return {
            'message': 'Files processed for chat context',
            'results': results,
            'conversation_id': conversation_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"File upload and processing failed: {str(e)}"
        )

@router.post("/upload_files_for_rag")
async def upload_files_for_rag(
    files: List[UploadFile] = File(...),
    course_id: str = Form(...),
    user_id: str = Form(...),
    rag_model: str | None = Form(None),
):
    try:
        results = await service.process_files_for_rag(files, course_id, user_id, rag_model)
        return {
            'message': 'Files processed for RAG knowledge base',
            'results': results,
            'course_id': course_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"RAG file upload and processing failed: {str(e)}"
        )



@router.post("/courses")
async def create_course(data: dict):
    """Create a new course"""
    try:
        from src.course.CRUD import create_course
        course = create_course(
            created_by=data.get('created_by', 'admin'),
            title=data.get('title', ''),
            description=data.get('description', ''),
            term=data.get('term', '')
        )
        return {"course": course}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating course: {str(e)}")


