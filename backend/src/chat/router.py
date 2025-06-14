from fastapi import APIRouter, Request, UploadFile, File, Form, Query, HTTPException, status
from . import service
from .models import ConversationBase, ConversationCreate, ConversationUpdate, ConversationOut

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