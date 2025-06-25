"""
Enhanced Supabase Vector Store Client

This module provides an enhanced Supabase vector store client with:
- Support for 768-dimensional embeddings (text-embedding-004)
- Enhanced metadata handling
- Better error handling and logging
- Additional utility methods for RAG operations
"""

from typing import Any, Dict, List, Optional
import logging
import json

try:
    from supabase import create_client, Client
except ImportError:  # pragma: no cover
    create_client = None
    Client = None

logger = logging.getLogger(__name__)


class SupabaseVectorStore:
    """
    Enhanced Supabase Vector Store for RAG applications.
    
    Features:
    - Supports 768-dimensional embeddings
    - Enhanced metadata handling
    - Similarity search with metadata
    - Document management
    - Health checks and statistics
    """
    
    def __init__(self, url: str, key: str, table: str = "documents"):
        """
        Initialize the Supabase vector store.
        
        Args:
            url: Supabase project URL
            key: Supabase service key
            table: Table name for storing documents
        """
        if create_client is None:
            raise RuntimeError("supabase-py not installed. Please install with: pip install supabase")
        
        self.client: Client = create_client(url, key)
        self.table = table
        self.url = url
        
        logger.info(f"Initialized SupabaseVectorStore with table: {table}")
    
    def add_texts(self, course_id: str, texts: List[str], embeds: List[List[float]]) -> None:
        """
        Add texts with embeddings to the vector store.
        
        Args:
            course_id: Course identifier
            texts: List of text chunks
            embeds: List of embedding vectors
        """
        try:
            for text, embedding in zip(texts, embeds):
                self.client.table(self.table).insert({
                    "course_id": course_id,
                    "text": text,
                    "embedding": embedding
                }).execute()
            
            logger.info(f"Added {len(texts)} texts to course {course_id}")
            
        except Exception as e:
            logger.error(f"Failed to add texts to vector store: {e}")
            raise
    
    async def add_texts_with_metadata(
        self, 
        course_id: str, 
        texts: List[str], 
        embeds: List[List[float]], 
        metadata_list: List[Dict[str, Any]]
    ) -> None:
        """
        Add texts with embeddings and metadata to the vector store.
        
        Args:
            course_id: Course identifier
            texts: List of text chunks
            embeds: List of embedding vectors
            metadata_list: List of metadata dictionaries
        """
        try:
            rows_to_insert = []
            for text, embedding, metadata in zip(texts, embeds, metadata_list):
                row = {
                    "course_id": course_id,
                    "text": text,
                    "embedding": embedding,
                    "metadata": metadata
                }
                rows_to_insert.append(row)
            
            # Insert in batches to avoid request size limits
            batch_size = 100
            for i in range(0, len(rows_to_insert), batch_size):
                batch = rows_to_insert[i:i + batch_size]
                self.client.table(self.table).insert(batch).execute()
                logger.debug(f"Inserted batch {i//batch_size + 1} of {(len(rows_to_insert) + batch_size - 1) // batch_size}")
            
            logger.info(f"Added {len(texts)} texts with metadata to course {course_id}")
            
        except Exception as e:
            logger.error(f"Failed to add texts with metadata to vector store: {e}")
            raise
    
    def similarity_search(
        self, 
        course_id: str, 
        query_emb: List[float], 
        limit: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search for course documents.
        
        Args:
            course_id: Course identifier
            query_emb: Query embedding vector
            limit: Maximum number of results
            
        Returns:
            List of matching documents
        """
        try:
            rpc_result = self.client.rpc(
                "match_documents",
                {
                    "query_embedding": query_emb,
                    "match_count": limit,
                    "course_id_param": course_id,
                },
            )
            
            data = rpc_result.execute().data
            logger.debug(f"Similarity search returned {len(data) if data else 0} results")
            return data or []
            
        except Exception as e:
            logger.error(f"Failed to perform similarity search: {e}")
            raise
    
    async def similarity_search_with_metadata(
        self, 
        course_id: str, 
        query_emb: List[float], 
        limit: int = 4,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search with metadata filtering.
        
        Args:
            course_id: Course identifier
            query_emb: Query embedding vector
            limit: Maximum number of results
            threshold: Minimum similarity threshold
            
        Returns:
            List of matching documents with metadata
        """
        try:
            # Use the enhanced RPC function that includes metadata
            rpc_result = self.client.rpc(
                "match_documents_with_metadata",
                {
                    "query_embedding": query_emb,
                    "match_count": limit,
                    "course_id_param": course_id,
                    "similarity_threshold": threshold,
                },
            )
            
            data = rpc_result.execute().data
            logger.debug(f"Enhanced similarity search returned {len(data) if data else 0} results")
            return data or []
            
        except Exception as e:
            # Fallback to basic similarity search if enhanced RPC doesn't exist
            logger.warning(f"Enhanced similarity search failed, falling back to basic search: {e}")
            return self.similarity_search(course_id, query_emb, limit)
    
    async def get_course_statistics(self, course_id: str) -> Dict[str, Any]:
        """
        Get statistics about a course's documents and chunks.
        
        Args:
            course_id: Course identifier
            
        Returns:
            Dictionary with course statistics
        """
        try:
            # Get total document count
            doc_count_result = self.client.table(self.table).select(
                "id", count="exact"
            ).eq("course_id", course_id).execute()
            
            total_chunks = doc_count_result.count or 0
            
            # Get unique document count
            unique_docs_result = self.client.table(self.table).select(
                "metadata->document_id", count="exact"
            ).eq("course_id", course_id).execute()
            
            # Get average chunk sizes
            chunks_result = self.client.table(self.table).select(
                "metadata->word_count", "metadata->char_count"
            ).eq("course_id", course_id).execute()
            
            word_counts = []
            char_counts = []
            
            if chunks_result.data:
                for chunk in chunks_result.data:
                    metadata = chunk.get('metadata', {})
                    if isinstance(metadata, str):
                        metadata = json.loads(metadata)
                    
                    word_count = metadata.get('word_count', 0)
                    char_count = metadata.get('char_count', 0)
                    
                    if word_count > 0:
                        word_counts.append(word_count)
                    if char_count > 0:
                        char_counts.append(char_count)
            
            statistics = {
                'total_chunks': total_chunks,
                'unique_documents': len(set(doc.get('metadata', {}).get('document_id') for doc in chunks_result.data)) if chunks_result.data else 0,
                'avg_word_count': sum(word_counts) / len(word_counts) if word_counts else 0,
                'avg_char_count': sum(char_counts) / len(char_counts) if char_counts else 0,
                'embedding_dimension': 768,  # text-embedding-004 dimension
            }
            
            logger.debug(f"Retrieved statistics for course {course_id}: {statistics}")
            return statistics
            
        except Exception as e:
            logger.error(f"Failed to get course statistics: {e}")
            raise
    
    async def delete_document(self, course_id: str, document_id: str) -> int:
        """
        Delete all chunks for a specific document.
        
        Args:
            course_id: Course identifier
            document_id: Document identifier
            
        Returns:
            Number of chunks deleted
        """
        try:
            # First, get the count of chunks to be deleted
            count_result = self.client.table(self.table).select(
                "id", count="exact"
            ).eq("course_id", course_id).eq("metadata->>document_id", document_id).execute()
            
            chunks_to_delete = count_result.count or 0
            
            if chunks_to_delete > 0:
                # Delete the chunks
                delete_result = self.client.table(self.table).delete().eq(
                    "course_id", course_id
                ).eq("metadata->>document_id", document_id).execute()
                
                logger.info(f"Deleted {chunks_to_delete} chunks for document {document_id}")
            
            return chunks_to_delete
            
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            raise
    
    async def delete_course(self, course_id: str) -> int:
        """
        Delete all documents and chunks for a course.
        
        Args:
            course_id: Course identifier
            
        Returns:
            Number of chunks deleted
        """
        try:
            # Get count of chunks to be deleted
            count_result = self.client.table(self.table).select(
                "id", count="exact"
            ).eq("course_id", course_id).execute()
            
            chunks_to_delete = count_result.count or 0
            
            if chunks_to_delete > 0:
                # Delete all chunks for the course
                delete_result = self.client.table(self.table).delete().eq(
                    "course_id", course_id
                ).execute()
                
                logger.info(f"Deleted {chunks_to_delete} chunks for course {course_id}")
            
            return chunks_to_delete
            
        except Exception as e:
            logger.error(f"Failed to delete course: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check of the Supabase connection.
        
        Returns:
            Dictionary with health status
        """
        try:
            # Test basic connectivity
            test_result = self.client.table(self.table).select("id").limit(1).execute()
            
            # Test RPC function availability
            rpc_available = True
            try:
                self.client.rpc("match_documents", {
                    "query_embedding": [0.0] * 768,
                    "match_count": 1,
                    "course_id_param": "health_check"
                }).execute()
            except Exception:
                rpc_available = False
            
            return {
                'healthy': True,
                'table_accessible': True,
                'rpc_function_available': rpc_available,
                'embedding_dimension': 768
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'healthy': False,
                'error': str(e)
            }
    
    def get_table_info(self) -> Dict[str, Any]:
        """
        Get information about the current table configuration.
        
        Returns:
            Dictionary with table information
        """
        return {
            'table_name': self.table,
            'url': self.url,
            'expected_embedding_dimension': 768,
            'client_initialized': self.client is not None
        }
