from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import sys
import os

# Add the project root to the path so we can import config
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from config.constants import ModelConfig, TextProcessingConfig

# Import document loaders for different file types
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
from langchain.chains import RetrievalQA
from langchain.schema import Document

# Import application settings and modular service clients
from app.config import Settings
from embedding.google_embedding_client import GoogleEmbeddingClient
from llm_clients.gemini_client import GeminiClient
from vector_db.supabase_client import SupabaseVectorClient


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
        
        # Initialize Gemini LLM client for question answering
        self.llm_client = GeminiClient(
            api_key=settings.google_api_key,
            model="gemini-2.5-pro",
            temperature=ModelConfig.DEFAULT_TEMPERATURE
        )
        
        # Initialize Supabase vector database client for storing and retrieving embeddings
        self.vector_client = SupabaseVectorClient(
            supabase_url=settings.supabase_url or "",
            supabase_service_role_key=settings.supabase_api_key or "",
            embeddings_client=self.embedding_client,
            table_name="document_embeddings"
        )
        
        # Create base retriever and QA chain (will be course-filtered when needed)
        self.base_retriever_config = {
            "search_type": "similarity_score_threshold",
            "search_kwargs": {
                "k": TextProcessingConfig.DEFAULT_RETRIEVAL_K,
                "score_threshold": TextProcessingConfig.DEFAULT_SCORE_THRESHOLD
            }
        }

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
            doc_id = doc_id or f"doc_{hash(content) % 10**10}"
            
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
            print(f"🚀 Starting stateless processing flow for file: {file_identifier}")
            
            # Step 1: Load - Pull raw file from Supabase Storage
            print("📁 Step 1: Loading file from storage...")
            # Note: In production, this would pull from Supabase Storage
            # For now, we'll work with the content directly
            
            # Step 2: Split - Use preset text splitting strategy
            print("✂️ Step 2: Splitting document into chunks...")
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
            print("🧠 Step 3: Generating embeddings with gemini-embedding-001...")
            
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
            print("💾 Step 4: Bulk-writing vectors to Supabase...")
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
            
            print("✅ Stateless processing flow completed successfully")
            print(f"   📊 Statistics: {len(chunks)} chunks, {model_info['output_dimensionality']}D vectors")
            
            return result
            
        except Exception as e:
            error_msg = f"❌ Processing flow failed: {str(e)}"
            print(error_msg)
            return {
                "file_identifier": file_identifier,
                "error": str(e),
                "success": False
            }

    def answer_question(self, course_id: str, question: str) -> Dict[str, Any]:
        """
        Answer a question using RAG with modular components.
        Retrieves relevant chunks and generates answer using LLM.
        
        Args:
            course_id: Identifier for the course
            question: The question text to be answered
            
        Returns:
            A dictionary with the answer, source information, and success status
        """

        try:
            print(f"DEBUG: Starting RAG query for course_id='{course_id}', question='{question[:100]}...'")
            
            # First, check what vectors exist in the database without any filters
            print("DEBUG: Checking all vectors in database...")
            try:
                all_vectors = self.vector_client.vector_store.similarity_search_with_relevance_scores(
                    query=question,
                    k=20  # Get more results to see what's in the database
                )
                print(f"DEBUG: Found {len(all_vectors)} total vectors in database (no filters):")
                for i, (doc, score) in enumerate(all_vectors):
                    print(f"  Vector {i+1}: score={score:.4f}, course_id='{doc.metadata.get('course_id', 'MISSING')}', content='{doc.page_content[:100]}...'")
            except Exception as e:
                print(f"DEBUG: Error checking all vectors: {e}")
            
            # Now try with course filter
            print(f"DEBUG: Searching for vectors with course_id='{course_id}'...")
            search_results = self.vector_client.similarity_search_with_score(
                query=question,
                k=TextProcessingConfig.DEFAULT_RETRIEVAL_K,
                filter={"course_id": course_id}
            )
            
            print(f"DEBUG: Retrieved {len(search_results)} vectors for course_id '{course_id}':")
            for i, (doc, score) in enumerate(search_results):
                print(f"  Vector {i+1}: score={score:.4f}, content='{doc.page_content[:100]}...'")
                if hasattr(doc, 'metadata') and doc.metadata:
                    print(f"    Metadata: {doc.metadata}")
            
            if len(search_results) == 0:
                print(f"DEBUG: No vectors found for course_id '{course_id}'. Trying without course filter...")
                # If no results with course filter, try without it
                search_results = self.vector_client.vector_store.similarity_search_with_relevance_scores(
                    query=question,
                    k=TextProcessingConfig.DEFAULT_RETRIEVAL_K
                )
                print(f"DEBUG: Found {len(search_results)} vectors without course filter:")
                for i, (doc, score) in enumerate(search_results):
                    print(f"  Vector {i+1}: score={score:.4f}, course_id='{doc.metadata.get('course_id', 'MISSING')}', content='{doc.page_content[:100]}...'")
            
            # Create retriever and QA chain
            qa_chain = self.create_course_qa_chain(course_id)
            
            # Generate answer using modular QA chain
            response = qa_chain.invoke({"query": question})
            
            # Format sources with detailed debug information
            sources = self._format_sources_with_debug(response.get("source_documents", []))
            
            debug_info = {
                "query": question,
                "course_id": course_id,
                "vectors_retrieved": len(search_results),
                "vector_scores": [{"index": i, "score": score, "content_preview": doc.page_content[:100]} 
                                 for i, (doc, score) in enumerate(search_results)]
            }
            
            return {
                "answer": response["result"],
                "sources": sources,
                "debug_info": debug_info,
                "success": True
            }
        except Exception as e:
            print(f"DEBUG: RAG query failed: {str(e)}")
            import traceback
            print(f"DEBUG: Full error traceback: {traceback.format_exc()}")
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

    def load_file(self, file_path: str) -> List[Document]:
        """
        Load documents from file using appropriate loader based on file extension.
        Supports .txt, .pdf, and .docx formats.
        
        Args:
            file_path: The path to the file to be loaded
        
        Returns:
            A list of Document objects loaded from the file
        """
        path = Path(file_path)
        if path.suffix == '.txt':
            loader = TextLoader(file_path)
        elif path.suffix == '.pdf':
            loader = PyPDFLoader(file_path)
        elif path.suffix == '.docx':
            loader = Docx2txtLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {path.suffix}")
        
        return loader.load()
    
    def create_course_retriever(self, course_id: str):
        """
        Create a course-specific retriever with metadata filtering.
        Restricts retrieval to documents matching the given course_id.
        
        Args:
            course_id: The ID of the course to filter documents by
        
        Returns:
            A retriever object configured to retrieve documents for the specified course
        """
        config = self.base_retriever_config.copy()
        config["search_kwargs"]["filter"] = {"course_id": course_id}
        
        return self.vector_client.as_retriever(**config)
    
    def create_course_qa_chain(self, course_id: str):
        """
        Create a course-specific QA chain using the retriever and LLM client.
        Enables retrieval-augmented generation for question answering.
        
        Args:
            course_id: The ID of the course to create the QA chain for
        
        Returns:
            A QA chain object configured for the specified course
        """
        retriever = self.create_course_retriever(course_id)
        
        return RetrievalQA.from_chain_type(
            llm=self.llm_client.get_llm_client(),
            retriever=retriever,
            return_source_documents=True
        )
