from fastapi import APIRouter, HTTPException, Query, Depends
from .models import MessageCreate, MessageUpdate, MessageResponse
from .service import (
    create_message_service, get_messages_service, get_message_service,
    update_message_service, delete_message_service, get_course_analytics_service
)
from typing import List
from src.auth.middleware import admin_required

router = APIRouter(
    prefix='/messages',
    tags=['messages']
)

@router.post("/", response_model=MessageResponse)
async def create_message_api(msg: MessageCreate):
    data = await create_message_service(msg)
    if data:
        return data[0]
    raise HTTPException(status_code=400, detail="Message not created")

@router.get("/conversation/{conversation_id}", response_model=List[MessageResponse])
async def get_messages_api(conversation_id: int):
    return await get_messages_service(conversation_id)

@router.get("/{message_id}", response_model=MessageResponse)
async def get_message_api(message_id: str):
    data = await get_message_service(message_id)
    if data:
        return data
    raise HTTPException(status_code=404, detail="Message not found")

@router.put("/{message_id}", response_model=MessageResponse)
async def update_message_api(message_id: str, msg: MessageUpdate):
    data = await update_message_service(message_id, msg)
    if data:
        return data[0]
    raise HTTPException(status_code=404, detail="Message not found")

@router.delete("/{message_id}")
async def delete_message_api(message_id: str):
    data = await delete_message_service(message_id)
    if data:
        return {"detail": "Message deleted"}
    raise HTTPException(status_code=404, detail="Message not found")


@router.get("/analytics/course/{course_id}")
async def get_course_analytics(course_id: str):
    return await get_course_analytics_service(course_id)

@router.post("/seed_test_data/{course_id}", dependencies=[Depends(admin_required)])
async def seed_test_messages(course_id: str):
    """Create some test messages for demo purposes"""
    from src.supabaseClient import supabase
    import uuid
    from datetime import datetime, timedelta, timezone
    
    # Create a test conversation
    conv_id = str(uuid.uuid4())
    test_messages = [
        {
            "message_id": str(uuid.uuid4()),
            "conversation_id": conv_id,
            "user_id": "test_student_1",
            "sender": "user",
            "content": "What is the difference between supervised and unsupervised learning?",
            "course_id": course_id,
            "model": "rag",
            "created_at": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        },
        {
            "message_id": str(uuid.uuid4()),
            "conversation_id": conv_id,
            "user_id": "test_student_1",
            "sender": "assistant",
            "content": "Supervised learning uses labeled training data to learn patterns, while unsupervised learning finds patterns in data without labels. In supervised learning, you have input-output pairs to train the model, like predicting house prices from features. Unsupervised learning discovers hidden structures, like clustering customers by behavior.",
            "course_id": course_id,
            "model": "rag",
            "created_at": (datetime.now(timezone.utc) - timedelta(days=2, hours=1)).isoformat()
        },
        {
            "message_id": str(uuid.uuid4()),
            "conversation_id": str(uuid.uuid4()),
            "user_id": "test_student_2",
            "sender": "user",
            "content": "Can you explain backpropagation in neural networks?",
            "course_id": course_id,
            "model": "gpt-4o",
            "created_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        },
        {
            "message_id": str(uuid.uuid4()),
            "conversation_id": str(uuid.uuid4()),
            "user_id": "test_student_2",
            "sender": "assistant",
            "content": "Backpropagation is the algorithm used to train neural networks. It works by calculating gradients of the loss function with respect to each weight, then updating weights to minimize error. The process flows backward through the network layers, hence 'backpropagation'.",
            "course_id": course_id,
            "model": "gpt-4o",
            "created_at": (datetime.now(timezone.utc) - timedelta(days=1, hours=1)).isoformat()
        }
    ]
    
    for msg in test_messages:
        supabase.table("messages").insert(msg).execute()
    
    return {"message": f"Created {len(test_messages)} test messages for course {course_id}"}