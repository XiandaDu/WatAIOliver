from fastapi import APIRouter, Request, UploadFile, File, Form, Query, HTTPException, status
from . import service
from .models import ConversationBase, ConversationCreate, ConversationUpdate, ConversationDelete, MessageCreate, MessageUpdate, MessageDelete
from . import CRUD as supabase_crud

router = APIRouter(
    prefix='/chat',
    tags=['chat']
)

@router.get("/")
async def chat(data: ConversationUpdate):
    return service.nebula_text_endpoint(data.message)

@router.post("/open_ask")
async def open_ask(data: ConversationBase):
    return service.open_ask(data)

@router.post("/create_conversation")
async def create_conversation(data: ConversationCreate):
    return supabase_crud.create_conversation(data)

@router.get("/conversations/{user_id}")
async def get_conversation(user_id: str):
    return supabase_crud.get_conversation(user_id)

@router.post("/update_conversation")
async def update_conversation(data: ConversationUpdate):
    return supabase_crud.update_conversation(data)

@router.post("/delete_conversation")
async def delete_conversation(data: ConversationDelete):
    return supabase_crud.delete_conversation(data)

@router.post("/create_message")
async def create_message(data: MessageCreate):
    return supabase_crud.create_message(data)

@router.get("/messages/{conversation_id}")
async def get_messages(conversation_id: str):
    return supabase_crud.get_messages(conversation_id)

@router.post("/update_message")
async def update_message(data: MessageUpdate):
    return supabase_crud.update_message(data)

@router.post("/delete_message")
async def delete_message(data: MessageDelete):
    return supabase_crud.delete_message(data)