from typing import Any, Dict, List

try:
    from supabase import create_client
except ImportError:  # pragma: no cover
    create_client = None


class SupabaseVectorStore:
    def __init__(self, url: str, key: str, table: str = "documents"):
        if create_client is None:
            raise RuntimeError("supabase-py not installed")
        self.client = create_client(url, key)
        self.table = table

    def add_texts(self, course_id: str, texts: List[str], embeds: List[List[float]]):
        for text, emb in zip(texts, embeds):
            self.client.table(self.table).insert(
                {"course_id": course_id, "text": text, "embedding": emb}
            ).execute()

    def similarity_search(self, course_id: str, query_emb: List[float], limit: int = 4) -> List[Dict[str, Any]]:
        rpc = self.client.rpc(
            "match_documents",
            {
                "query_embedding": query_emb,
                "match_count": limit,
                "course_id_param": course_id,
            },
        )
        data = rpc.execute().data  # type: ignore
        return data or []
