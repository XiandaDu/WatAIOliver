from db.client import supabase


def create_course_model(course_id: str, model_id: str):
    data = {"course_id": course_id, "model_id": model_id}
    response = supabase.table("course_models").insert(data).execute()
    return response.data[0] if response.data else None


def read_course_models(course_id: str):
    response = (
        supabase.table("course_models").select("*").eq("course_id", course_id).execute()
    )
    return response.data


def delete_course_model(course_id: str, model_id: str):
    response = (
        supabase.table("course_models")
        .delete()
        .eq("course_id", course_id)
        .eq("model_id", model_id)
        .execute()
    )
    return response.data
