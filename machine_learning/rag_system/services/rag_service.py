from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
from langchain.chains import RetrievalQA
from langchain.schema import Document
from supabase import create_client

from app.config import Settings


class RAGService:
    def __init__(self, settings: Settings):
        self.settings = settings
        
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=settings.google_api_key
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        supabase = create_client(settings.supabase_url, settings.supabase_key)
        self.vector_store = SupabaseVectorStore(
            client=supabase,
            embedding=self.embeddings,
            table_name="documents"
        )
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=settings.google_api_key,
            temperature=0.1
        )
        
        self.retriever = self.vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": 4, "score_threshold": 0.7}
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.retriever,
            return_source_documents=True
        )

    def process_document(self, course_id: str, content: str, doc_id: str = None) -> Dict[str, Any]:
        try:
            doc_id = doc_id or f"doc_{hash(content) % 10**10}"
            
            document = Document(
                page_content=content,
                metadata={"course_id": course_id, "document_id": doc_id}
            )
            
            chunks = self.text_splitter.split_documents([document])
            
            for i, chunk in enumerate(chunks):
                chunk.metadata.update({
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                })
            
            self.vector_store.add_documents(chunks)
            
            return {
                "document_id": doc_id,
                "chunks_created": len(chunks),
                "success": True
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    def answer_question(self, course_id: str, question: str) -> Dict[str, Any]:
        try:
            retriever_with_filter = self.vector_store.as_retriever(
                search_kwargs={"filter": {"course_id": course_id}, "k": 4}
            )
            
            docs_with_scores = self.vector_store.similarity_search_with_score(
                question, 
                k=4,
                filter={"course_id": course_id}
            )
            
            response = self.qa_chain({"query": question})
            
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
