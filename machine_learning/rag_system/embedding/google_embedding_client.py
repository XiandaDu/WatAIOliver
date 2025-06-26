from typing import List
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document


class GoogleEmbeddingClient:
    """Google AI embeddings client with text splitting capabilities."""
    
    def __init__(self, api_key: str, model: str = "models/text-embedding-004"):
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=model,
            google_api_key=api_key
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks."""
        return self.text_splitter.split_documents(documents)
    
    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query."""
        return self.embeddings.embed_query(text)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple documents."""
        return self.embeddings.embed_documents(texts)
    
    def get_embeddings_client(self):
        """Get the underlying LangChain embeddings client."""
        return self.embeddings 