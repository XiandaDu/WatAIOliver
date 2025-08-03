from fastapi import APIRouter, HTTPException
from src.supabaseClient import supabase

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

@router.get("/stats")
async def get_usage_stats():
    """Get overall usage statistics"""
    try:
        # Get conversations count
        conversations = supabase.table("conversations").select("*").execute()
        total_conversations = len(conversations.data) if conversations.data else 0

        # Get messages count
        messages = supabase.table("messages").select("*").execute()
        total_messages = len(messages.data) if messages.data else 0

        # Get active users count
        users = supabase.table("users").select("*").execute()
        active_users = len([u for u in users.data if u.get("last_login_at")]) if users.data else 0

        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "active_users": active_users
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/all")
async def get_all_users():
    """Get all users"""
    try:
        response = supabase.table("users").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages/all")
async def get_all_messages():
    """Get all messages"""
    try:
        response = supabase.table("messages").select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))