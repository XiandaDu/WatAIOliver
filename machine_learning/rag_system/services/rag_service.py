"""
Enhanced RAG Service

This service provides a complete RAG pipeline using:
- Google's text-embedding-004 model (768 dimensions)
- Supabase vector database
- Improved chunking and preprocessing
- Better document management and retrieval
"""

from typing import List, Dict, Any, Optional
import logging
import asyncio
from datetime import datetime

from ..app.config import Settings
from ..embedding.gemini_embedding_client import GeminiEmbeddingClient
from ..llm_clients.gemini_client import GeminiClient
from ..vector_db.supabase_client import SupabaseVectorStore
from .text_processing import TextProcessingService, ChunkingConfig, ChunkMetadata

logger = logging.getLogger(__name__)


class RAGService:
    """
    Enhanced RAG Service with improved chunking and processing.
    
    Features:
    - Uses text-embedding-004 (768 dimensions)
    - Adaptive chunking with semantic boundaries
    - Proper preprocessing pipeline
    - Enhanced metadata tracking
    - Better error handling and logging
    """
    
    def __init__(self, settings: Settings, chunking_config: ChunkingConfig = None):
        """
        Initialize the RAG service.
        
        Args:
            settings: Application settings
            chunking_config: Configuration for text chunking
        """
        self.settings = settings
        self.embedding_client = GeminiEmbeddingClient(settings.gemini_api_key)
        self.llm_client = GeminiClient(settings.gemini_api_key)
        self.vector_store = SupabaseVectorStore(
            url=settings.supabase_url,
            key=settings.supabase_key,
        )
        self.text_processor = TextProcessingService(chunking_config)
        
        # Log initialization
        embedding_dim = self.embedding_client.get_embedding_dimension()
        logger.info(f"Initialized RAG Service with {embedding_dim}D embeddings")

    async def process_document(
        self, 
        course_id: str, 
        content: str, 
        document_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process a document for RAG ingestion with improved chunking.
        
        Args:
            course_id: Course identifier
            content: Document content
            document_id: Optional document identifier
            metadata: Optional additional metadata
            
        Returns:
            Dictionary with processing results and statistics
        """
        start_time = datetime.now()
        
        try:
            if not content or not content.strip():
                raise ValueError("Document content cannot be empty")
            
            # Use document_id or generate one
            doc_id = document_id or f"doc_{hash(content) % 10**10}"
            logger.info(f"Processing document {doc_id} for course {course_id}")
            
            # Process and chunk the document
            chunks_with_metadata = self.text_processor.process_document(content, doc_id)
            
            if not chunks_with_metadata:
                raise ValueError("No chunks were generated from the document")
            
            # Extract chunks and prepare for embedding
            chunk_texts = [chunk_text for chunk_text, _ in chunks_with_metadata]
            chunk_metadatas = [chunk_metadata for _, chunk_metadata in chunks_with_metadata]
            
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(chunk_texts)} chunks")
            embeddings = await self.embedding_client.embed_documents(chunk_texts)
            
            # Prepare enhanced metadata for vector storage
            enhanced_metadata = []
            for i, chunk_metadata in enumerate(chunk_metadatas):
                chunk_meta = {
                    'course_id': course_id,
                    'document_id': doc_id,
                    'chunk_index': chunk_metadata.chunk_index,
                    'total_chunks': chunk_metadata.total_chunks,
                    'word_count': chunk_metadata.word_count,
                    'char_count': chunk_metadata.char_count,
                    'start_char': chunk_metadata.start_char,
                    'end_char': chunk_metadata.end_char,
                    'processed_at': start_time.isoformat(),
                }
                
                # Add any additional metadata
                if metadata:
                    chunk_meta.update(metadata)
                    
                enhanced_metadata.append(chunk_meta)
            
            # Store in vector database
            logger.info(f"Storing {len(chunk_texts)} chunks in vector database")
            await self.vector_store.add_texts_with_metadata(
                course_id, chunk_texts, embeddings, enhanced_metadata
            )
            
            # Generate statistics
            processing_time = (datetime.now() - start_time).total_seconds()
            statistics = self.text_processor.get_chunk_statistics(chunks_with_metadata)
            
            result = {
                'document_id': doc_id,
                'course_id': course_id,
                'chunks_created': len(chunk_texts),
                'processing_time_seconds': processing_time,
                'embedding_dimension': len(embeddings[0]) if embeddings else 0,
                'statistics': statistics,
                'success': True
            }
            
            logger.info(f"Successfully processed document {doc_id}: {len(chunk_texts)} chunks in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Failed to process document: {e}")
            return {
                'document_id': doc_id if 'doc_id' in locals() else 'unknown',
                'course_id': course_id,
                'error': str(e),
                'processing_time_seconds': processing_time,
                'success': False
            }

    async def answer_question(
        self, 
        course_id: str, 
        question: str, 
        top_k: int = 4,
        similarity_threshold: float = 0.7,
        include_metadata: bool = False
    ) -> Dict[str, Any]:
        """
        Answer a question using RAG with enhanced retrieval.
        
        Args:
            course_id: Course identifier
            question: User question
            top_k: Number of chunks to retrieve
            similarity_threshold: Minimum similarity threshold
            include_metadata: Whether to include chunk metadata in response
            
        Returns:
            Dictionary with answer and retrieval information
        """
        start_time = datetime.now()
        
        try:
            if not question or not question.strip():
                raise ValueError("Question cannot be empty")
            
            logger.info(f"Answering question for course {course_id}: {question[:100]}...")
            
            # Generate query embedding
            query_embedding = await self.embedding_client.embed_query(question)
            
            # Retrieve relevant documents
            retrieved_docs = await self.vector_store.similarity_search_with_metadata(
                course_id, query_embedding, limit=top_k, threshold=similarity_threshold
            )
            
            if not retrieved_docs:
                return {
                    'answer': "I couldn't find relevant information to answer your question.",
                    'question': question,
                    'course_id': course_id,
                    'retrieved_chunks': 0,
                    'processing_time_seconds': (datetime.now() - start_time).total_seconds(),
                    'success': True
                }
            
            # Prepare context from retrieved documents
            context_parts = []
            metadata_info = []
            
            for doc in retrieved_docs:
                context_parts.append(doc.get('text', ''))
                if include_metadata:
                    metadata_info.append({
                        'document_id': doc.get('document_id'),
                        'chunk_index': doc.get('chunk_index'),
                        'similarity_score': doc.get('similarity', 0),
                        'word_count': doc.get('word_count', 0)
                    })
            
            context = "\n\n".join(context_parts)
            
            # Generate answer using LLM
            logger.info(f"Generating answer using {len(retrieved_docs)} retrieved chunks")
            answer = await self.llm_client.generate(question, context)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                'answer': answer,
                'question': question,
                'course_id': course_id,
                'retrieved_chunks': len(retrieved_docs),
                'processing_time_seconds': processing_time,
                'success': True
            }
            
            if include_metadata:
                result['chunk_metadata'] = metadata_info
            
            logger.info(f"Successfully answered question in {processing_time:.2f}s using {len(retrieved_docs)} chunks")
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Failed to answer question: {e}")
            return {
                'error': str(e),
                'question': question,
                'course_id': course_id,
                'processing_time_seconds': processing_time,
                'success': False
            }

    async def get_course_statistics(self, course_id: str) -> Dict[str, Any]:
        """
        Get statistics about a course's documents and chunks.
        
        Args:
            course_id: Course identifier
            
        Returns:
            Dictionary with course statistics
        """
        try:
            stats = await self.vector_store.get_course_statistics(course_id)
            return {
                'course_id': course_id,
                'statistics': stats,
                'success': True
            }
        except Exception as e:
            logger.error(f"Failed to get course statistics: {e}")
            return {
                'course_id': course_id,
                'error': str(e),
                'success': False
            }

    async def delete_document(self, course_id: str, document_id: str) -> Dict[str, Any]:
        """
        Delete a document and all its chunks from the vector store.
        
        Args:
            course_id: Course identifier
            document_id: Document identifier
            
        Returns:
            Dictionary with deletion results
        """
        try:
            deleted_count = await self.vector_store.delete_document(course_id, document_id)
            logger.info(f"Deleted document {document_id}: {deleted_count} chunks removed")
            return {
                'course_id': course_id,
                'document_id': document_id,
                'chunks_deleted': deleted_count,
                'success': True
            }
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return {
                'course_id': course_id,
                'document_id': document_id,
                'error': str(e),
                'success': False
            }

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check of all RAG components.
        
        Returns:
            Dictionary with health status
        """
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'components': {},
            'overall_healthy': True
        }
        
        # Check embedding client
        try:
            test_embedding = await self.embedding_client.embed_query("test")
            health_status['components']['embedding'] = {
                'healthy': True,
                'dimension': len(test_embedding),
                'model': self.embedding_client.model
            }
        except Exception as e:
            health_status['components']['embedding'] = {
                'healthy': False,
                'error': str(e)
            }
            health_status['overall_healthy'] = False
        
        # Check vector store
        try:
            await self.vector_store.health_check()
            health_status['components']['vector_store'] = {'healthy': True}
        except Exception as e:
            health_status['components']['vector_store'] = {
                'healthy': False,
                'error': str(e)
            }
            health_status['overall_healthy'] = False
        
        # Check LLM client
        try:
            test_response = await self.llm_client.generate("Test question", "Test context")
            health_status['components']['llm'] = {
                'healthy': True,
                'response_length': len(test_response)
            }
        except Exception as e:
            health_status['components']['llm'] = {
                'healthy': False,
                'error': str(e)
            }
            health_status['overall_healthy'] = False
        
        return health_status
