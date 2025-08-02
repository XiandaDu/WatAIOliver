import os
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document
import openai
from machine_learning.constants import TextProcessingConfig, ModelConfig


class OpenAIEmbeddingClient:
    """OpenAI embeddings client supporting the v3 and ada models."""

    def __init__(self, api_key: str | None = None, model: str = "text-embedding-3-small"):
        openai.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise ValueError("OPENAI_API_KEY must be provided")
        self.model = model
        # All embedding models are projected to a unified dimension
        if model == "text-embedding-3-large":
            self.output_dimensionality = ModelConfig.OPENAI_LARGE_DIMENSIONALITY
        else:
            self.output_dimensionality = ModelConfig.OPENAI_SMALL_DIMENSIONALITY
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=TextProcessingConfig.DEFAULT_CHUNK_SIZE,
            chunk_overlap=TextProcessingConfig.DEFAULT_CHUNK_OVERLAP,
            separators=TextProcessingConfig.CHUNK_SEPARATORS,
        )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        return self.text_splitter.split_documents(documents)

    def embed_query(self, text: str) -> List[float]:
        response = openai.embeddings.create(
            input=[text], model=self.model, dimensions=self.output_dimensionality
        )
        return response.data[0].embedding if response.data else []

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        response = openai.embeddings.create(
            input=texts, model=self.model, dimensions=self.output_dimensionality
        )
        return [d.embedding for d in response.data]

    def get_model_info(self) -> dict:
        return {
            "model": self.model,
            "expected_dimensionality": self.output_dimensionality,
            "chunk_size": self.text_splitter._chunk_size,
            "chunk_overlap": self.text_splitter._chunk_overlap,
        }
