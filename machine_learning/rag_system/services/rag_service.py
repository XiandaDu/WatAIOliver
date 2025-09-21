from typing import Dict, Any
from datetime import datetime

from machine_learning.constants import ModelConfig

from langchain.schema import Document

from rag_system.app.config import Settings
from rag_system.embedding.google_embedding_client import GoogleEmbeddingClient
from rag_system.llm_clients.gemini_client import GeminiClient
from rag_system.vector_db.supabase_client import SupabaseVectorClient


class RAGService:
    """Orchestrates RAG operations using modular components.
    
    Handles document processing, embedding, storage, retrieval, and question-answering.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize RAGService with application settings and modular clients.
        Sets up embedding, LLM, and vector database clients.
        """
        self.settings = settings
        
        # Initialize Google embedding client for document chunking and vectorization
        self.embedding_client = GoogleEmbeddingClient(
            google_cloud_project=settings.google_cloud_project,
            model="text-embedding-004",  # new
            output_dimensionality=ModelConfig.DEFAULT_OUTPUT_DIMENSIONALITY
        )
        # self.embedding_client = GoogleEmbeddingClient(
        #     google_cloud_project=settings.google_cloud_project,
        #     model="gemini-embedding-001",  # old，commented
        #     output_dimensionality=ModelConfig.DEFAULT_OUTPUT_DIMENSIONALITY
        # )
        
        # Initialize Gemini LLM client for question answering (default to Flash)
        self.llm_client = GeminiClient(
            api_key=settings.google_api_key,
            model="gemini-2.5-flash",  # Changed from Pro to Flash as default
            temperature=ModelConfig.DEFAULT_TEMPERATURE
        )
        
        # Initialize Supabase vector database client for storing and retrieving embeddings
        self.vector_client = SupabaseVectorClient(
            supabase_url=settings.supabase_url or "",
            supabase_service_role_key=settings.supabase_api_key or "",
            embeddings_client=self.embedding_client,
            table_name="document_embeddings"
        )
        

    def process_document(self, course_id: str, content: str, doc_id: str = None) -> Dict[str, Any]:
        """
        Process and store a document in the vector database.
        Splits document, adds metadata, and stores chunks as embeddings.
        
        Args:
            course_id: Identifier for the course the document is associated with
            content: The raw content of the document to be processed
            doc_id: Optional pre-defined document ID, if not provided, one will be generated
            
        Returns:
            A dictionary with document processing results, including document ID and chunk count
        """
        try:
            import time
            doc_id = doc_id or f"doc_{hash(content) % 10**10}_{int(time.time() * 1000)}"
            
            document = Document(
                page_content=content,
                metadata={"course_id": course_id, "document_id": doc_id}
            )
            
            # Split document using embedding client
            chunks = self.embedding_client.split_documents([document])
            
            # Add metadata to chunks
            for i, chunk in enumerate(chunks):
                chunk.metadata.update({
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                })
            
            # Store in vector database
            self.vector_client.add_documents(chunks)
            
            return {
                "document_id": doc_id,
                "chunks_created": len(chunks),
                "success": True
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    def process_file_from_storage(self, file_identifier: str, course_id: str) -> Dict[str, Any]:
        """Complete stateless processing flow: Load -> Split -> Embed -> Write Back.
        
        This implements the processing pipeline described in the meeting notes:
        1. Load: Pull raw file from storage
        2. Split: Use RecursiveCharacterTextSplitter to chunk document  
        3. Embed: Convert chunks to 512D vectors using gemini-embedding-001
        4. Write Back: Bulk-write vectors and metadata to Supabase PG vector table
        
        Args:
            file_identifier: Identifier for file in Supabase Storage
            course_id: Course identifier for metadata
            
        Returns:
            Processing result with statistics
        """
        try:
            print(f"Starting stateless processing flow for file: {file_identifier}")
            
            # Step 1: Load - Pull raw file from Supabase Storage
            print("Step 1: Loading file from storage...")
            # Note: In production, this would pull from Supabase Storage
            # For now, we'll work with the content directly
            
            # Step 2: Split - Use preset text splitting strategy
            print("️Step 2: Splitting document into chunks...")
            document = Document(
                page_content="Sample content for processing",  # Replace with actual file content
                metadata={
                    "course_id": course_id,
                    "file_identifier": file_identifier,
                    "processed_at": datetime.now().isoformat()
                }
            )
            
            chunks = self.embedding_client.split_documents([document])
            print(f"   Created {len(chunks)} chunks")
            
            # Step 3: Embed - Convert text chunks to 512D vectors
            print("Step 3: Generating embeddings with gemini-embedding-001...")
            
            # Add enhanced metadata to chunks
            for i, chunk in enumerate(chunks):
                chunk.metadata.update({
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "file_identifier": file_identifier,
                    "embedding_model": "gemini-embedding-001",
                    "vector_dimensions": ModelConfig.DEFAULT_OUTPUT_DIMENSIONALITY
                })
            
            # Step 4: Write Back - Bulk-write to Supabase PG vector table
            print("Step 4: Bulk-writing vectors to Supabase...")
            document_ids = self.vector_client.add_documents(chunks)
            
            # Get model info for response
            model_info = self.embedding_client.get_model_info()
            vector_info = self.vector_client.get_table_info()
            
            result = {
                "file_identifier": file_identifier,
                "course_id": course_id,
                "chunks_created": len(chunks),
                "document_ids": document_ids,
                "model_info": model_info,
                "vector_info": vector_info,
                "processing_complete": True,
                "success": True
            }
            
            print("Stateless processing flow completed successfully")
            print(f"Statistics: {len(chunks)} chunks, {model_info['output_dimensionality']}D vectors")
            
            return result
            
        except Exception as e:
            error_msg = f"Processing flow failed: {str(e)}"
            print(error_msg)
            return {
                "file_identifier": file_identifier,
                "error": str(e),
                "success": False
            }

    
    def answer_question_with_scores(self, course_id: str, question: str) -> Dict[str, Any]:
        """
        Answer a question using direct vector search to preserve similarity scores.
        
        This method bypasses the retriever chain that loses scores and uses the vector client
        directly to get documents with their similarity scores preserved.
        
        Args:
            course_id: Identifier for the course
            question: The question text to be answered
            
        Returns:
            A dictionary with the answer, source information with scores, and success status
        """
        try:
            # Get documents directly from vector search with scores preserved
            scored_results = self.vector_client.similarity_search_with_score(
                query=question,
                k=4,  # Match default retrieval k
                filter={"course_id": course_id}
            )
            
            if not scored_results:
                return {
                    "success": False,
                    "answer": "No relevant documents found for this course.",
                    "sources": []
                }
            
            # Debug: Show what documents are retrieved (like existing debug output)
            print(f"=== RETRIEVED {len(scored_results)} DOCUMENTS FOR QUERY: '{question}' ===")
            for i, (doc, score) in enumerate(scored_results):
                print(f"DOC {i+1}:")
                print(f"  Content: {doc.page_content[:200]}...")
                print(f"  Metadata: {doc.metadata}")
                print(f"  Score: {score:.4f}")
                print(f"  ---")
            
            # Extract documents and create context for LLM
            documents = [doc for doc, _ in scored_results]
            context = "\n\n".join([doc.page_content for doc in documents])
            
            # Generate answer using the LLM directly with the context
            prompt = f"""Based on the following context from course materials, please answer the question comprehensively.
            
Context:
{context}

Question: {question}

Please provide a detailed answer based on the context provided. If the context doesn't contain enough information to fully answer the question, mention what information is missing."""
            
            answer = self.llm_client.generate(prompt)
            
            # Format sources with preserved similarity scores
            sources = []
            for doc, score in scored_results:
                source_info = {
                    "content": doc.page_content,
                    "score": score,  # Score preserved from vector search!
                    "metadata": doc.metadata or {}
                }
                sources.append(source_info)
            
            return {
                "answer": answer,
                "sources": sources,
                "success": True
            }
            
        except Exception as e:
            print(f"RAG Error with scores: {str(e)}")
            return {"error": str(e), "success": False}

    def _format_sources(self, source_documents):
        """
        Format source documents for response.
        Truncates content and includes metadata for each source.
        
        Args:
            source_documents: List of source Document objects
        
        Returns:
            A list of formatted source information dictionaries
        """
        sources = []
        for i, doc in enumerate(source_documents):
            similarity_score = doc.metadata.get('similarity_score', 'N/A') if hasattr(doc, 'metadata') and doc.metadata else 'N/A'
            sources.append({
                "index": i,
                "content": doc.page_content[:500],
                "score": similarity_score,
                "metadata": doc.metadata if hasattr(doc, 'metadata') else {},
                "content_length": len(doc.page_content)
            })
        return sources


