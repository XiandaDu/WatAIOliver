from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
from langchain.chains import RetrievalQA
from langchain.schema import Document

from app.config import Settings
from embedding.google_embedding_client import GoogleEmbeddingClient
from llm_clients.gemini_client import GeminiClient
from vector_db.supabase_client import SupabaseVectorClient


class RAGService:
    """Orchestrates RAG operations using modular components."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        
        # Initialize modular components
        self.embedding_client = GoogleEmbeddingClient(
            api_key=settings.google_api_key,
            model="models/text-embedding-004"
        )
        
        self.llm_client = GeminiClient(
            api_key=settings.google_api_key,
            model="gemini-1.5-flash",
            temperature=0.1
        )
        
        self.vector_client = SupabaseVectorClient(
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_key,
            embeddings_client=self.embedding_client.get_embeddings_client(),
            table_name="documents"
        )
        
        # Create retriever and QA chain
        self.retriever = self.vector_client.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": 4, "score_threshold": 0.7}
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm_client.get_llm_client(),
            retriever=self.retriever,
            return_source_documents=True
        )

    def process_document(self, course_id: str, content: str, doc_id: str = None) -> Dict[str, Any]:
        """Process and store a document in the vector database."""
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

    def answer_question(self, course_id: str, question: str) -> Dict[str, Any]:
        """Answer a question using RAG."""
        try:
            # Get similar documents with scores
            docs_with_scores = self.vector_client.similarity_search_with_score(
                question, 
                k=4,
                filter={"course_id": course_id}
            )
            
            # Generate answer using QA chain
            response = self.qa_chain({"query": question})
            
            # Format sources
            sources = []
            if docs_with_scores:
                for doc, score in docs_with_scores:
                    sources.append({
                        "content": doc.page_content[:200],
                        "score": score,
                        "metadata": doc.metadata
                    })
            
            return {
                "answer": response["result"],
                "sources": sources,
                "success": True
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    def load_file(self, file_path: str) -> List[Document]:
        """Load documents from file."""
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
