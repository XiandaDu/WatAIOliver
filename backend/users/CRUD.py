from supabaseClient import supabase
from datetime import datetime, timezone

# CREATE
def create_user(user_id, username, email, role="student"):
    data = {
        "user_id": user_id,
        "username": username,
        "email": email,
        "role": role,
    }
    response = supabase.table("users").insert(data).execute()
    return response.data

# READ (get all users)
def get_users():
    response = supabase.table("users").select("*").execute()
    return response.data

# READ (get user by id)
def get_user_by_id(user_id):
    response = supabase.table("users").select("*").eq("user_id", user_id).execute()
    return response.data

# UPDATE (update message by id)
def update_user(user_id, username=None, email=None, role=None):
    data = {
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    if username is not None:
        data["username"] = username
    if email is not None:
        data["email"] = email
    if role is not None:
        data["role"] = role
    response = supabase.table("users").update(data).eq("user_id", user_id).execute()
    return response.data

# DELETE (delete user by id)
def delete_user(user_id):
    response = supabase.table("users").delete().eq("user_id", user_id).execute()
    return response.data