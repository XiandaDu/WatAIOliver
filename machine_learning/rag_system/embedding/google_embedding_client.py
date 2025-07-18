import os
from typing import List
import sys
# Import text splitter for chunking documents
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document
# Import Google GenAI SDK for embedding
from google import genai
from google.genai.types import EmbedContentConfig

# Add the project root to the path so we can import config
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from config.constants import TextProcessingConfig, ModelConfig


class GoogleEmbeddingClient:
    """Google AI embeddings client using gemini-embedding-001 following official documentation.
    
    Handles text chunking and embedding generation for queries and documents.
    """

    def __init__(self, google_cloud_project: str, model: str = "gemini-embedding-001", output_dimensionality: int = ModelConfig.DEFAULT_OUTPUT_DIMENSIONALITY):
        """Initialize the embedding client with gemini-embedding-001.
        
        Args:
            google_cloud_project: Google Cloud project ID for Vertex AI
            model: Embedding model to use (default: gemini-embedding-001)
            output_dimensionality: Target vector dimensions (default: 512)
        """
        self.google_cloud_project = google_cloud_project
        self.model = model
        self.output_dimensionality = output_dimensionality
        
        # Use Vertex AI with service account credentials for gemini-embedding-001
        self.client = genai.Client()
        
        # Initialize text splitter for document chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=TextProcessingConfig.DEFAULT_CHUNK_SIZE,
            chunk_overlap=TextProcessingConfig.DEFAULT_CHUNK_OVERLAP,
            separators=TextProcessingConfig.CHUNK_SEPARATORS
        )
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks for embedding.
        Uses langchain's RecursiveCharacterTextSplitter.
        
        Args:
            documents: List of langchain Document objects
        
        Returns:
            List of chunked Document objects
        """
        return self.text_splitter.split_documents(documents)
    
    def embed_query(self, text: str) -> List[float]: 
        """
        Generate embedding for a single query string.
        
        Args:
            text: Query text
        
        Returns:
            Embedding vector as a list of floats
        """
        response = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config=EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=self.output_dimensionality,
            ),
        )
        # Return embedding vals if present, else empty list
        return response.embeddings[0].values if response.embeddings else []
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple documents.
        
        Args:
            texts: List of document strings
        
        Returns:
            List of embedding vectors
        """
        results = []
        for text in texts:
            response = self.client.models.embed_content(
                model=self.model,
                contents=text,
                config=EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                    output_dimensionality=self.output_dimensionality,
                ),
            )
            if response.embeddings:
                results.append(response.embeddings[0].values)
        return results
    
    def get_model_info(self) -> dict:
        """
        Get information about the current model configuration.
        
        Returns:
            Dictionary with model details
        """
        return {
            "model": self.model,
            "expected_dimensionality": self.output_dimensionality,
            "chunk_size": self.text_splitter._chunk_size,
            "chunk_overlap": self.text_splitter._chunk_overlap
        } 