from typing import List

from ..app.config import Settings
from ..embedding.gemini_embedding_client import GeminiEmbeddingClient
from ..llm_clients.gemini_client import GeminiClient
from ..vector_db.supabase_client import SupabaseVectorStore


class RAGService:
    def __init__(self, settings: Settings):
        self.embedding_client = GeminiEmbeddingClient(settings.gemini_api_key)
        self.llm_client = GeminiClient(settings.gemini_api_key)
        self.vector_store = SupabaseVectorStore(
            url=settings.supabase_url,
            key=settings.supabase_key,
        )

    async def process_document(self, course_id: str, content: str) -> None:
        chunks = self._split_text(content)
        embeddings = await self.embedding_client.embed_documents(chunks)
        self.vector_store.add_texts(course_id, chunks, embeddings)

    async def answer_question(self, course_id: str, question: str) -> str:
        q_embedding = await self.embedding_client.embed_query(question)
        docs = self.vector_store.similarity_search(course_id, q_embedding)
        context = "\n".join([d["text"] for d in docs])
        return await self.llm_client.generate(question, context)

    @staticmethod
    def _split_text(text: str, chunk_size: int = 500) -> List[str]:
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
