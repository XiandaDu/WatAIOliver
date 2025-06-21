from supabase_client import supabase

# CREATE
def create_file(user_id, file_name, file_type, file_size, file_path, description=None, course_id=None):
    data = {
        "user_id": user_id,
        "file_name": file_name,
        "file_type": file_type,
        "file_size": file_size,
        "file_path": file_path,
        "description": description,
        "course_id": course_id,
    }
    response = supabase.table("t_file").insert(data).execute()
    return response.data

# READ (get all files for a user)
def get_files(user_id):
    response = supabase.table("t_file").select("*").eq("user_id", user_id).order("created_at", desc=False).execute()
    return response.data

# UPDATE (update file by id)
def update_file(file_id, **kwargs):
    response = supabase.table("t_file").update(kwargs).eq("id", file_id).execute()
    return response.data

# DELETE (delete file by id)
def delete_file(file_id):
    response = supabase.table("t_file").delete().eq("id", file_id).execute()
    return response.data 