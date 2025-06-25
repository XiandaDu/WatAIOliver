from typing import List, Optional
import logging

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover - if package not installed
    genai = None

logger = logging.getLogger(__name__)


class GeminiEmbeddingClient:
    """
    Google Gemini Embedding Client using text-embedding-004 model.
    Produces 768-dimensional embeddings as per Google's documentation.
    """
    
    def __init__(
        self, 
        api_key: str, 
        model: str = "models/text-embedding-004", 
        transport: str = "rest"
    ):
        """
        Initialize the Gemini embedding client.
        
        Args:
            api_key: Google API key
            model: Embedding model name (default: text-embedding-004 for 768 dimensions)
            transport: Transport method for API calls
        """
        self.api_key = api_key
        self.model = model
        if genai is not None:
            genai.configure(api_key=api_key, transport=transport)
        logger.info(f"Initialized GeminiEmbeddingClient with model: {model}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for document chunks.
        
        Args:
            texts: List of text chunks to embed
            
        Returns:
            List of 768-dimensional embedding vectors
        """
        if genai is None:
            raise RuntimeError("google-generativeai not installed")
        
        results: List[List[float]] = []
        logger.info(f"Generating embeddings for {len(texts)} document chunks")
        
        for i, text in enumerate(texts):
            try:
                resp = genai.embed_content(
                    model=self.model, 
                    content=text, 
                    task_type="RETRIEVAL_DOCUMENT"
                )
                embedding = resp["embedding"]
                results.append(embedding)
                
                if i % 10 == 0:  # Log progress every 10 embeddings
                    logger.debug(f"Generated embedding {i+1}/{len(texts)}")
                    
            except Exception as e:
                logger.error(f"Failed to generate embedding for text {i}: {e}")
                raise
                
        logger.info(f"Successfully generated {len(results)} embeddings")
        return results

    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a query.
        
        Args:
            text: Query text to embed
            
        Returns:
            768-dimensional embedding vector
        """
        if genai is None:
            raise RuntimeError("google-generativeai not installed")
        
        try:
            resp = genai.embed_content(
                model=self.model, 
                content=text, 
                task_type="RETRIEVAL_QUERY"
            )
            embedding = resp["embedding"]
            logger.debug(f"Generated query embedding (dimension: {len(embedding)})")
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            raise

    def get_embedding_dimension(self) -> int:
        """
        Returns the embedding dimension for the current model.
        text-embedding-004 produces 768-dimensional vectors.
        """
        if "text-embedding-004" in self.model:
            return 768
        elif "text-embedding-005" in self.model:
            return 768
        elif "text-multilingual-embedding-002" in self.model:
            return 768
        else:
            # Default assumption for Google embedding models
            return 768
