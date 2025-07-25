from typing import List, Dict, Any, Tuple, Optional
# Import Supabase vector store integration for LangChain
from langchain_community.vectorstores import SupabaseVectorStore
from langchain.schema import Document
# Import Supabase Python client for database connection
from supabase import create_client


class SupabaseVectorClient:
    """Supabase vector database client optimized for 512-dimensional vectors."""
    

    def __init__(self, supabase_url: str, supabase_service_role_key: str, embeddings_client, table_name: str = "document_embeddings"):
        """
        Initialize Supabase vector client and vector store.
        
        Args:
            supabase_url: Supabase project URL
            supabase_service_role_key: Supabase service key
            embeddings_client: Embedding client (should output 512-dimensional vectors)
            table_name: Vector table name (default: "documents")
        """
        self.supabase = create_client(supabase_url, supabase_service_role_key)
        self.embeddings_client = embeddings_client
        self.table_name = table_name
        
        # Create vector store with enhanced configuration for 512D vectors
        self.vector_store = SupabaseVectorStore(
            client=self.supabase,
            embedding=embeddings_client,
            table_name=table_name,
            # Note: Vector column dimension should be set to 512 in Supabase
            # CREATE TABLE documents (
            #   id bigserial primary key,
            #   content text,
            #   metadata jsonb,
            #   embedding vector(512)  -- 512 dimensions for cost/performance optimization
            # );
        )
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        Add documents to the vector store with bulk operation.
        
        Args:
            documents: List of Document objects
        
        Returns:
            List of document IDs that were added
        """
        try:
            # Bulk write operation as specified in meeting notes
            result = self.vector_store.add_documents(documents)
            print(f"Successfully added {len(documents)} documents to vector store")
            return result
        except Exception as e:
            print(f"Failed to add documents: {e}")
            raise
    
    def similarity_search(self, query: str, k: int = 4, filter: Optional[Dict[str, Any]] = None) -> List[Document]:
        """
        Search for similar documents using vector similarity.
        
        Args:
            query: Query string
            k: Number of results to return
            filter: Optional metadata filter
        
        Returns:
            List of Document objects
        """
        try:
            if filter:
                return self.vector_store.similarity_search(query, k=k, filter=filter)
            return self.vector_store.similarity_search(query, k=k)
        except Exception as e:
            print(f"Similarity search failed: {e}")
            raise
    
    def similarity_search_with_score(self, query: str, k: int = 4, filter: Optional[Dict[str, Any]] = None) -> List[Tuple[Document, float]]:
        """Search for similar documents with similarity scores.
        
        This implements the secondary filtering logic mentioned in meeting notes.
        Uses SupabaseVectorStore's similarity_search_with_relevance_scores method.
        """
        try:
            # Use the correct method for SupabaseVectorStore
            if filter:
                results = self.vector_store.similarity_search_with_relevance_scores(query, k=k, filter=filter)
            else:
                results = self.vector_store.similarity_search_with_relevance_scores(query, k=k)
            
            # Enhanced filtering with metadata and score thresholds
            filtered_results = []
            for doc, score in results:
                # Add score to metadata for better debugging
                if doc.metadata is None:
                    doc.metadata = {}
                doc.metadata['similarity_score'] = score
                filtered_results.append((doc, score))
            
            print(f"Retrieved {len(filtered_results)} documents with similarity scores")
            return filtered_results
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Similarity search with score failed: {e}")
            print(f"Full error details: {error_details}")
            raise
    
    def as_retriever(self, search_type: str = "similarity_score_threshold", search_kwargs: Optional[Dict[str, Any]] = None):
        """
        Get retriever for the vector store with enhanced configuration.
        Allows for custom search type and keyword arguments.
        
        Args:
            search_type: Type of search (default: similarity_score_threshold)
            search_kwargs: Additional search parameters
        
        Returns:
            Retriever object
        """
        if search_kwargs is None:
            # Optimized for 512-dimensional vectors
            search_kwargs = {
                "k": 4, 
                "score_threshold": 0.7,
                # Additional metadata for filtering
                "fetch_k": 20  # Fetch more candidates for better filtering
            }
        
        return self.vector_store.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs
        )
    
    def get_vector_store(self):
        """Get the underlying LangChain vector store."""
        return self.vector_store
    
    def get_table_info(self) -> Dict[str, Any]:
        """
        Get information about the vector table configuration.
        
        Returns:
            Dictionary with table details and expected configuration
        """
        return {
            "table_name": self.table_name,
            "expected_dimensions": 512,
            "indexing": "HNSW/ivfflat optimized for 512D",
            "note": "Vector column should be configured as vector(512) in Supabase"
        } 