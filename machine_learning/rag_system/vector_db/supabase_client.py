from typing import List, Dict, Any, Tuple
from langchain_community.vectorstores import SupabaseVectorStore
from langchain.schema import Document
from supabase import create_client


class SupabaseVectorClient:
    """Supabase vector database client."""
    
    def __init__(self, supabase_url: str, supabase_key: str, embeddings_client, table_name: str = "documents"):
        self.supabase = create_client(supabase_url, supabase_key)
        self.embeddings_client = embeddings_client
        
        self.vector_store = SupabaseVectorStore(
            client=self.supabase,
            embedding=embeddings_client,
            table_name=table_name
        )
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the vector store."""
        self.vector_store.add_documents(documents)
    
    def similarity_search(self, query: str, k: int = 4, filter: Dict[str, Any] = None) -> List[Document]:
        """Search for similar documents."""
        if filter:
            return self.vector_store.similarity_search(query, k=k, filter=filter)
        return self.vector_store.similarity_search(query, k=k)
    
    def similarity_search_with_score(self, query: str, k: int = 4, filter: Dict[str, Any] = None) -> List[Tuple[Document, float]]:
        """Search for similar documents with similarity scores."""
        if filter:
            return self.vector_store.similarity_search_with_score(query, k=k, filter=filter)
        return self.vector_store.similarity_search_with_score(query, k=k)
    
    def as_retriever(self, search_type: str = "similarity_score_threshold", search_kwargs: Dict[str, Any] = None):
        """Get retriever for the vector store."""
        if search_kwargs is None:
            search_kwargs = {"k": 4, "score_threshold": 0.7}
        
        return self.vector_store.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs
        )
    
    def get_vector_store(self):
        """Get the underlying LangChain vector store."""
        return self.vector_store 