from fastapi import APIRouter, Request, UploadFile, File, Form, Query, HTTPException, status
from fastapi.responses import Response, JSONResponse
from . import service
from .models import ConversationCreate, ConversationUpdate, ConversationDelete, MessageCreate, MessageUpdate, MessageDelete, ConversationOut, MessageOut, ChatRequest
from . import CRUD as supabase_crud

router = APIRouter(
    prefix='/chat',
    tags=['chat']
)

@router.options("/create_conversation")
async def create_conversation_options():
    return Response(
        content="",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.options("/conversations/{user_id}")
async def get_conversations_options():
    return Response(
        content="",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.options("/delete_conversation")
async def delete_conversation_options():
    return Response(
        content="",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.options("/update_conversation")
async def update_conversation_options():
    return Response(
        content="",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.options("/create_message")
async def create_message_options():
    return Response(
        content="",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.options("/messages/{conversation_id}")
async def get_messages_options():
    return Response(
        content="",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.options("/")
async def chat_options():
    return Response(
        content="",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.options("")
async def chat_root_options():
    return Response(
        content="",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.post("/")
async def chat(data: ChatRequest):
    result = service.nebula_text_endpoint(data)
    return JSONResponse(
        content={"result": result},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.post("")
async def chat_root(data: ChatRequest):
    result = service.nebula_text_endpoint(data)
    return JSONResponse(
        content={"result": result},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.post("/open_ask")
async def open_ask(data: ConversationCreate):
    return service.open_ask(data)

@router.post("/create_conversation")
async def create_conversation(data: ConversationCreate, response_model=ConversationOut):
    result = supabase_crud.create_conversation(data)
    return JSONResponse(
        content=result,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.get("/conversations/{user_id}")
async def get_conversations(user_id: str, response_model=ConversationOut):
    result = supabase_crud.get_conversations(user_id)
    return JSONResponse(
        content=result,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.post("/update_conversation")
async def update_conversation(data: ConversationUpdate, response_model=ConversationOut):
    result = supabase_crud.update_conversation(data)
    return JSONResponse(
        content=result,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.post("/delete_conversation")
async def delete_conversation(data: ConversationDelete, response_model=ConversationOut):
    result = supabase_crud.delete_conversation(data)
    return JSONResponse(
        content=result,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.post("/create_message")
async def create_message(data: MessageCreate, response_model=MessageOut):
    result = supabase_crud.create_message(data)
    return JSONResponse(
        content=result,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.get("/messages/{conversation_id}")
async def get_messages(conversation_id: str, response_model=MessageOut):
    result = supabase_crud.get_messages(conversation_id)
    return JSONResponse(
        content=result,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    )

@router.post("/update_message")
async def update_message(data: MessageUpdate, response_model=MessageOut):
    return supabase_crud.update_message(data)

@router.post("/delete_message")
async def delete_message(data: MessageDelete, response_model=MessageOut):
    return supabase_crud.delete_message(data)