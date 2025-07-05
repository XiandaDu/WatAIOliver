from fastapi import APIRouter, HTTPException, Query
from .models import MessageCreate, MessageUpdate, MessageResponse
from .service import (
    create_message_service, get_messages_service, get_message_service,
    update_message_service, delete_message_service
)
from typing import List
from fastapi.encoders import jsonable_encoder

router = APIRouter(
    prefix='/messages',
    tags=['messages']
)

@router.post("/", response_model=MessageResponse)
async def create_message_api(msg: MessageCreate):
    data = await create_message_service(msg)
    if data:
        return jsonable_encoder(data[0])  # Ensures datetime fields are serialized
    raise HTTPException(status_code=400, detail="Message not created")

@router.get("/conversation/{conversation_id}", response_model=List[MessageResponse])
async def get_messages_api(conversation_id: str):
    return get_messages_service(conversation_id)  

@router.get("/{message_id}", response_model=MessageResponse)
async def get_message_api(message_id: str):
    data = get_message_service(message_id)  
    if data:
        return data
    raise HTTPException(status_code=404, detail="Message not found") # This line was added to handle the case where the message is not found

@router.put("/{message_id}", response_model=MessageResponse)
async def update_message_api(message_id: str, msg: MessageUpdate):
    data = update_message_service(message_id, msg)  
    if data:
        return data[0]
    raise HTTPException(status_code=404, detail="Message not found")

@router.delete("/{message_id}")
async def delete_message_api(message_id: str):
    data = delete_message_service(message_id)  
    if data:
        return {"detail": "Message deleted"}
    raise HTTPException(status_code=404, detail="Message not found")