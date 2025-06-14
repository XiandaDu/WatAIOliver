from fastapi import APIRouter, Request, UploadFile, File, Form, Query, HTTPException, status
from . import service

router = APIRouter(
    prefix='/chat',
    tags=['chat']
)

@router.get("/")
async def chat(request: Request, question: str):
    # question = "explain newton's laws of physics."
    return service.nebula_text_endpoint(question)
