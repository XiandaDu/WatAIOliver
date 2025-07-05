from src.supabaseClient import supabase

# CREATE
def create_course(user_id, name, notes=None, doc=None, model=None, prompt=None):
    data = {
        "user_id": user_id,
        "name": name,
        "notes": notes,
        "doc": doc,
        "model": model,
        "prompt": prompt,
    }
    response = supabase.table("t_course").insert(data).execute()
    return response.data

# READ (get all courses for a user)
def get_courses(user_id):
    response = supabase.table("t_course").select("*").eq("user_id", user_id).order("create_time", desc=False).execute()
    return response.data

# UPDATE (update course by id)
def update_course(course_id, **kwargs):
    response = supabase.table("t_course").update(kwargs).eq("id", course_id).execute()
    return response.data

# DELETE (delete course by id)
def delete_course(course_id):
    response = supabase.table("t_course").delete().eq("id", course_id).execute()
    return response.data