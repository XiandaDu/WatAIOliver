from src.supabaseClient import supabase
from datetime import datetime, timezone

# CREATE
def create_document(document_id, course_id, term, title, content):
    now = datetime.now(timezone.utc).isoformat()
    data = {
        "document_id": document_id,
        "course_id": course_id,
        "term": term,
        "title": title,
        "content": content,
        "created_at": now,
        "updated_at": now,
    }
    response = supabase.table("documents").insert(data).execute()
    return response.data

# READ (all or by course_id)
def get_documents(course_id=None):
    query = supabase.table("documents").select("*")
    if course_id:
        query = query.eq("course_id", course_id)
    response = query.order("created_at", desc=False).execute()
    return response.data

# READ single document by document_id
def get_document(document_id):
    response = supabase.table("documents").select("*").eq("document_id", document_id).single().execute()
    return response.data

# UPDATE
def update_document(document_id, **kwargs):
    kwargs["updated_at"] = datetime.now(timezone.utc).isoformat()
    response = supabase.table("documents").update(kwargs).eq("document_id", document_id).execute()
    return response.data

# DELETE
def delete_document(document_id):
    response = supabase.table("documents").delete().eq("document_id", document_id).execute()
    return response.data