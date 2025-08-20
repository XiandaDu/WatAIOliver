from .CRUD import (
    create_document, get_documents, get_document,
    update_document, delete_document
)
from .model import DocumentCreate, DocumentUpdate, DocumentResponse
from src.supabaseClient import supabase
from typing import List, Dict, Any

def create_document_service(doc_data: DocumentCreate):
    return create_document(
        doc_data.document_id,
        doc_data.course_id,
        doc_data.term,
        doc_data.title,
        doc_data.content
    )

def get_documents_service(course_id=None):
    return get_documents(course_id)

def get_document_service(document_id):
    return get_document(document_id)

def update_document_service(document_id, doc_data: DocumentUpdate):
    return update_document(document_id, **doc_data.dict(exclude_unset=True))

def delete_document_service(document_id):
    return delete_document(document_id)


def get_kb_documents_service(course_id: str) -> List[Dict[str, Any]]:
    """List knowledge-base documents for a course from vector table by aggregating metadata.

    Returns items like: { document_id, chunks }
    """
    if not course_id:
        return []
    # Fetch chunks filtered by course_id using JSON contains
    resp = supabase.table("document_embeddings").select("metadata").contains("metadata", {"course_id": course_id}).execute()
    rows = resp.data or []
    counts: Dict[str, int] = {}
    for r in rows:
        md = r.get("metadata") or {}
        doc_id = md.get("document_id") or "unknown"
        counts[doc_id] = counts.get(doc_id, 0) + 1
    return [{"document_id": k, "chunks": v} for k, v in counts.items()]


def delete_kb_document_service(course_id: str, document_id: str) -> Dict[str, Any]:
    """Delete all chunks for a KB document from vector table.

    Matches rows where metadata->>'course_id' and metadata->>'document_id'.
    """
    if not course_id or not document_id:
        return {"deleted": 0}
    # Supabase Python client lacks direct JSON path delete; use RPC or filter by contains
    # Use contains to scope by course_id then client-side filter id list
    resp = supabase.table("document_embeddings").select("id, metadata").contains("metadata", {"course_id": course_id}).execute()
    rows = resp.data or []
    ids_to_delete = [r["id"] for r in rows if (r.get("metadata") or {}).get("document_id") == document_id]
    deleted = 0
    if ids_to_delete:
        # Delete in batches
        for chunk in [ids_to_delete[i:i+100] for i in range(0, len(ids_to_delete), 100)]:
            supabase.table("document_embeddings").delete().in_("id", chunk).execute()
            deleted += len(chunk)
    return {"deleted": deleted}