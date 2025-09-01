from typing import Dict, Any, Optional
from datetime import datetime

from machine_learning.constants import ModelConfig, TextProcessingConfig

from langchain.chains import RetrievalQA
from langchain.schema import Document
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

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
        
        # Create base retriever and QA chain (will be course-filtered when needed)
        self.base_retriever_config = {
            "search_type": "similarity_score_threshold",
            "search_kwargs": {
                "k": TextProcessingConfig.DEFAULT_RETRIEVAL_K,
                "score_threshold": TextProcessingConfig.DEFAULT_SCORE_THRESHOLD
            }
        }
        
        # Initialize conversation memory for context
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Create structured prompt template
        self.qa_prompt = PromptTemplate(
            input_variables=["context", "question"],
            template="""You are a helpful AI assistant for academic course content. Use the provided context to answer the student's question accurately and concisely.

Context from course materials:
{context}

Student's question: {question}

Please provide a clear, educational response based on the context. If the context doesn't contain enough information to answer the student's question fully, acknowledge this and provide what you can from the available material.

Answer:"""
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

    def answer_question(self, course_id: str, question: str) -> Dict[str, Any]:
        """
        Answer a question using RetrievalQA chain with langchain.
        
        Args:
            course_id: Identifier for the course
            question: The question text to be answered
            
        Returns:
            A dictionary with the answer, source information, and success status
        """
        try:
            # Use langchain RetrievalQA for structured QA
            qa_chain = self.create_course_qa_chain(course_id)
            
            # Debug: Get retriever and show what documents are retrieved
            retriever = self.create_course_retriever(course_id)
            retrieved_docs = retriever.get_relevant_documents(question)
            print(f"=== RETRIEVED {len(retrieved_docs)} DOCUMENTS FOR QUERY: '{question}' ===")
            for i, doc in enumerate(retrieved_docs):
                print(f"DOC {i+1}:")
                print(f"  Content: {doc.page_content[:200]}...")
                print(f"  Metadata: {doc.metadata}")
                print(f"  ---")
            
            # Run the chain
            result = qa_chain({"query": question})
            
            # Extract answer and sources
            answer = result.get("result", "I couldn't find relevant information to answer your question.")
            source_docs = result.get("source_documents", [])
            
            # Format sources with similarity scores if available
            sources = []
            for doc in source_docs:
                source_info = {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                }
                # Add similarity score if available in metadata
                if hasattr(doc, 'metadata') and doc.metadata and 'similarity_score' in doc.metadata:
                    source_info["similarity_score"] = doc.metadata['similarity_score']
                sources.append(source_info)
            
            return {
                "answer": answer,
                "sources": sources,
                "success": True
            }
        except Exception as e:
            print(f"RAG Error: {str(e)}")
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
        
        # Try course-specific search first, fallback to global if no results
        try:
            # Test if retriever returns results for a dummy query
            test_docs = retriever.get_relevant_documents("test")
            if not test_docs:
                print(f"No course-specific docs for {course_id}, using global retriever")
                retriever = self.vector_client.as_retriever(**self.base_retriever_config)
        except:
            # Fallback to global retriever on any error
            retriever = self.vector_client.as_retriever(**self.base_retriever_config)
        
        return RetrievalQA.from_chain_type(
            llm=self.llm_client.get_llm_client(),
            retriever=retriever,
            return_source_documents=True,
            chain_type="stuff",
            chain_type_kwargs={
                "prompt": self.qa_prompt
            }
        )
