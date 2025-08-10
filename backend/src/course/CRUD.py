from src.supabaseClient import supabase
import uuid
from typing import Optional

# CREATE
def create_course(created_by, title, description=None, term=None, prompt=None, invite_code: Optional[str] = None):
    data = {
        "course_id": str(uuid.uuid4()),
        "title": title,
        "description": description,
        "term": term,
        "created_by": created_by,
        "prompt": prompt,
    }
    if invite_code is not None:
        data["invite_code"] = invite_code
    response = supabase.table("courses").insert(data).execute()
    return response.data[0] if response.data else None

# READ (get all courses for a user)
def get_courses(created_by):
    response = supabase.table("courses").select("*").eq("created_by", created_by).order("created_at", desc=False).execute()
    return response.data

# READ (get all courses - admin only)
def get_all_courses():
    response = supabase.table("courses").select("*").order("created_at", desc=False).execute()
    return response.data

# READ (get single course by id)
def get_course(course_id):
    response = supabase.table("courses").select("*").eq("course_id", course_id).execute()
    return response.data[0] if response.data else None

# READ (get single course by invite code)
def get_course_by_invite_code(invite_code: str):
    response = supabase.table("courses").select("*").eq("invite_code", invite_code).execute()
    return response.data[0] if response.data else None

def search_courses(created_by, search_term):
    response = supabase.table("courses").select("*").eq("created_by", created_by).ilike("title", f"%{search_term}%").execute()
    return response.data

def get_course_count(created_by):
    response = supabase.table("courses").select("course_id").eq("created_by", created_by).execute()
    return len(response.data) if response.data else 0

# UPDATE (update course by id)
def update_course(course_id, **kwargs):
    response = supabase.table("courses").update(kwargs).eq("course_id", course_id).execute()
    return response.data[0] if response.data else None

# DELETE (delete course by id)
def delete_course(course_id):
    response = supabase.table("courses").delete().eq("course_id", course_id).execute()
    return response.data

def find_course_by_title_ilike(title: str):
    resp = supabase.table("courses").select("*").ilike("title", f"%{title}%").execute()
    if resp.data:
        return resp.data[0]
    return None