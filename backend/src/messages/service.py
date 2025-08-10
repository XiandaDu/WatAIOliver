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
    """Aggregate analytics for a course using the messages table.

    Returns:
      - total_conversations: distinct conversations for the course
      - active_users: distinct users who sent at least one message
      - usage_by_day: last 7 days, count of messages per day
      - conversations_by_model: assistant message counts grouped by model
      - recent_pairs: latest anonymized Q&A pairs
    """
    logger.info(f"Fetching analytics for course: {course_id}")
    
    resp = supabase.table("messages").select("*").eq("course_id", course_id).order("created_at", desc=False).execute()
    msgs: List[Dict[str, Any]] = resp.data or []
    
    logger.info(f"Found {len(msgs)} messages for course {course_id}")
    
    # Log sample message structure for debugging
    if msgs:
        sample_msg = msgs[0]
        logger.info(f"Sample message structure: {sample_msg}")
        logger.info(f"Message keys: {list(sample_msg.keys()) if sample_msg else 'No messages'}")

    conversations = set()
    users = set()
    by_day: Dict[str, int] = {}
    model_counts: Dict[str, int] = {}

    for m in msgs:
        conversations.add(m.get("conversation_id"))
        if m.get("user_id"):
            users.add(m.get("user_id"))
        ts = m.get("created_at")
        if ts:
            day = str(ts)[:10]
            by_day[day] = by_day.get(day, 0) + 1
        if m.get("sender") == "assistant":
            model = m.get("model") or "unknown"
            model_counts[model] = model_counts.get(model, 0) + 1

    logger.info(f"Processed data - Conversations: {len(conversations)}, Users: {len(users)}, Days: {len(by_day)}, Models: {len(model_counts)}")
    logger.info(f"Usage by day: {by_day}")
    logger.info(f"Model counts: {model_counts}")

    today = datetime.now(timezone.utc).date()
    labels = []
    counts = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        key = d.isoformat()
        labels.append(d.strftime("%a"))
        counts.append(by_day.get(key, 0))

    recent_pairs: List[Dict[str, str]] = []
    for m in msgs[-200:]:
        if m.get("sender") == "user":
            recent_pairs.append({"user": m.get("content", ""), "assistant": ""})
        elif m.get("sender") == "assistant" and recent_pairs:
            if recent_pairs[-1].get("assistant", "") == "":
                recent_pairs[-1]["assistant"] = m.get("content", "")

    recent_pairs = [
        {"user": p.get("user", "")[:300], "assistant": p.get("assistant", "")[:600]}
        for p in recent_pairs[-25:]
    ]

    result = {
        "total_conversations": len([c for c in conversations if c]),
        "active_users": len([u for u in users if u]),
        "usage_by_day": {"labels": labels, "counts": counts},
        "conversations_by_model": model_counts,
        "recent_pairs": recent_pairs,
    }
    
    logger.info(f"Course analytics result for {course_id}: {result}")
    return result