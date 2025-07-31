from typing import List, Dict, Any, Tuple

from langchain.schema import Document

from rag_system.app.config import Settings
from rag_system.embedding.google_embedding_client import GoogleEmbeddingClient
from rag_system.embedding.openai_embedding_client import OpenAIEmbeddingClient
from rag_system.vector_db.supabase_client import SupabaseVectorClient
from machine_learning.constants import ModelConfig, TextProcessingConfig


class RetrievalService:
    """Service responsible for document storage and retrieval."""

    def __init__(self, settings: Settings, embedding_model: str | None = None):
        self.settings = settings
        model_name = embedding_model or settings.embedding_model
        if model_name.startswith("text-embedding-3") or model_name == "text-embedding-ada-002":
            self.embedding_client = OpenAIEmbeddingClient(
                api_key=settings.openai_api_key,
                model=model_name,
            )
        else:
            self.embedding_client = GoogleEmbeddingClient(
                google_cloud_project=settings.google_cloud_project,
                model=model_name,
            )
        self.vector_client = SupabaseVectorClient(
            supabase_url=settings.supabase_url or "",
            supabase_service_role_key=settings.supabase_api_key or "",
            embeddings_client=self.embedding_client,
            table_name="document_embeddings",
        )
        self.base_retriever_config = {
            "search_type": "similarity_score_threshold",
            "search_kwargs": {
                "k": TextProcessingConfig.DEFAULT_RETRIEVAL_K,
                "score_threshold": TextProcessingConfig.DEFAULT_SCORE_THRESHOLD,
            },
        }

    def process_document(self, course_id: str, content: str, doc_id: str | None = None) -> Dict[str, Any]:
        """Split and store a document in the vector database."""
        try:
            doc_id = doc_id or f"doc_{hash(content) % 10**10}"
            document = Document(page_content=content, metadata={"course_id": course_id, "document_id": doc_id})
            chunks = self.embedding_client.split_documents([document])
            for i, chunk in enumerate(chunks):
                chunk.metadata.update({"chunk_index": i, "total_chunks": len(chunks)})
            self.vector_client.add_documents(chunks)
            return {"document_id": doc_id, "chunks_created": len(chunks), "success": True}
        except Exception as e:
            return {"error": str(e), "success": False}

    def search_documents(self, course_id: str, query: str) -> List[Tuple[Document, float]]:
        """Retrieve relevant documents for a query."""
        return self.vector_client.similarity_search_with_score(
            query=query,
            k=TextProcessingConfig.DEFAULT_RETRIEVAL_K,
            filter={"course_id": course_id},
        )

    def format_sources(self, docs: List[Tuple[Document, float]]) -> List[Dict[str, Any]]:
        sources = []
        for i, (doc, score) in enumerate(docs):
            if doc.metadata is None:
                doc.metadata = {}
            doc.metadata["similarity_score"] = float(score)
            sources.append({
                "index": i,
                "content": doc.page_content[:500],
                "score": float(score),
                "metadata": doc.metadata,
            })
        return sources
