from .CRUD import (
    create_message, get_messages, get_message,
    update_message, delete_message
)
from .models import MessageCreate, MessageUpdate
from src.supabaseClient import supabase
from src.logger import logger
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

async def create_message_service(msg_data: MessageCreate):
    return await create_message(
        msg_data.message_id,
        msg_data.user_id,
        msg_data.content,
        msg_data.sender,
        msg_data.conversation_id,
        msg_data.course_id,
        msg_data.model
    )

async def get_messages_service(conversation_id):
    return await get_messages(conversation_id)

async def get_message_service(message_id):
    return await get_message(message_id)

async def update_message_service(message_id, msg_data: MessageUpdate):
    return await update_message(message_id, **msg_data.dict(exclude_unset=True))

async def delete_message_service(message_id):
    return await delete_message(message_id)


async def get_course_analytics_service(course_id: str) -> Dict[str, Any]:
    """Aggregate analytics for a course using SQL for counts and groupings."""
    logger.info(f"Fetching analytics for course: {course_id}")

    # Use SQL RPC to compute counts, group-bys, and usage by day
    rpc_resp = supabase.rpc('get_course_analytics_counts', { 'p_course_id': course_id }).execute()
    rpc_data: Dict[str, Any] = rpc_resp.data or {}

    result = {
        "total_conversations": rpc_data.get("total_conversations", 0),
        "active_users": rpc_data.get("active_users", 0),
        "usage_by_day": rpc_data.get("usage_by_day", {"labels": [], "counts": []}),
        "conversations_by_model": rpc_data.get("conversations_by_model", {}),
    }

    logger.info(f"Course analytics result for {course_id}: {result}")
    return result