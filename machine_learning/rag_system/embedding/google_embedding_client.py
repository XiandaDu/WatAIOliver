import os
from typing import List
import sys
# Import text splitter for chunking documents
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document
# Import Google GenAI SDK for embedding
from google import genai
from google.genai.types import EmbedContentConfig
from config.constants import TextProcessingConfig, ModelConfig


class GoogleEmbeddingClient:
    """Google AI embeddings client using gemini text-embedding-004 following official documentation."""
    
    def __init__(self, google_cloud_project: str, model: str = "text-embedding-004", output_dimensionality: int = ModelConfig.DEFAULT_OUTPUT_DIMENSIONALITY):
        """Initialize the embedding client with gemini text-embedding-004.
        
        Args:
            google_cloud_project: Google Cloud project ID for Vertex AI
            model: Embedding model to use (default: text-embedding-004)
            output_dimensionality: Target vector dimensions (default: 768)
        """
        self.google_cloud_project = google_cloud_project
        self.model = model
        self.output_dimensionality = output_dimensionality
        
        # Use Vertex AI with service account credentials for gemini text-embedding-004
        self.client = genai.Client()
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=TextProcessingConfig.DEFAULT_CHUNK_SIZE,
            chunk_overlap=TextProcessingConfig.DEFAULT_CHUNK_OVERLAP,
            separators=TextProcessingConfig.CHUNK_SEPARATORS
        )
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks."""
        return self.text_splitter.split_documents(documents)
    
    def embed_query(self, text: str) -> List[float]: 
        """Generate embedding for a single query."""
        response = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config=EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=self.output_dimensionality,
            ),
        )
        
        return response.embeddings[0].values if response.embeddings else []
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple documents."""
        # gemini text-embedding-004 supports one instance per request
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
        """Get information about the current model configuration."""
        return {
            "model": self.model,
            "expected_dimensionality": self.output_dimensionality,
            "chunk_size": self.text_splitter._chunk_size,
            "chunk_overlap": self.text_splitter._chunk_overlap
        }

# =============================================================================
# LEGACY CODE - gemini-embedding-001 (COMMENTED OUT)
# =============================================================================
# class GoogleEmbeddingClient:
#     """Google AI embeddings client using gemini-embedding-001 following official documentation."""
#     def __init__(self, google_cloud_project: str, model: str = "gemini-embedding-001", output_dimensionality: int = 512):
#         self.google_cloud_project = google_cloud_project
#         self.model = model
#         self.output_dimensionality = output_dimensionality
#         self.client = genai.Client()
#         self.text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=TextProcessingConfig.DEFAULT_CHUNK_SIZE,
#             chunk_overlap=TextProcessingConfig.DEFAULT_CHUNK_OVERLAP,
#             separators=TextProcessingConfig.CHUNK_SEPARATORS
#         ) 