from typing import List
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document
import google.generativeai as genai


class GoogleEmbeddingClient:
    """Google AI embeddings client with automatic latest model detection."""
    
    def __init__(self, api_key: str, model: str = None, output_dimensionality: int = 512):
        """Initialize the embedding client with Google's latest embedding model.
        
        Args:
            api_key: Google API key
            model: Embedding model to use (auto-detects latest if None)
            output_dimensionality: Target vector dimensions (default: 512)
        """
        self.api_key = api_key
        self.output_dimensionality = output_dimensionality
        
        # Configure the genai client for model listing
        genai.configure(api_key=api_key)
        
        # Auto-detect latest model if not specified
        if model is None:
            model = self._find_latest_embedding_model()
        
        self.model = model
        
        # Try different model names to find one that works
        model_candidates = [
            model,
            "models/embedding-001", 
            "models/text-embedding-004",
            "models/text-embedding-gecko-001"
        ]
        
        self.embeddings = None
        last_error = None
        
        for candidate in model_candidates:
            try:
                print(f"🔍 Trying model: {candidate}")
                self.embeddings = GoogleGenerativeAIEmbeddings(
                    model=candidate,
                    google_api_key=api_key,
                    task_type="retrieval_document"
                )
                self.model = candidate
                print(f"✅ Successfully initialized with: {candidate}")
                break
            except Exception as e:
                last_error = e
                print(f"⚠️ Failed with {candidate}: {str(e)[:100]}...")
                continue
        
        if self.embeddings is None:
            raise Exception(f"Failed to initialize any embedding model. Last error: {last_error}")
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def _find_latest_embedding_model(self) -> str:
        """Find the latest available embedding model."""
        try:
            models = genai.list_models()
            embedding_models = []
            
            for model in models:
                model_name = model.name
                # Check if model supports embedContent method
                if hasattr(model, 'supported_generation_methods'):
                    methods = model.supported_generation_methods
                    if 'embedContent' in methods:
                        embedding_models.append(model_name)
            
            # Priority order for latest models
            priority_models = [
                "models/embedding-001",
                "models/text-embedding-gecko-001",  
                "models/text-embedding-004"
            ]
            
            # Find the first available priority model
            for priority_model in priority_models:
                if priority_model in embedding_models:
                    return priority_model
            
            # If no priority models found, return the first embedding model
            if embedding_models:
                return embedding_models[0]
            
        except Exception as e:
            print(f"⚠️ Could not auto-detect model: {e}")
        
        # Fallback to a known working model
        return "models/text-embedding-004"
    
    @staticmethod
    def list_available_models(api_key: str) -> List[str]:
        """List all available models from Google AI."""
        try:
            genai.configure(api_key=api_key)
            models = genai.list_models()
            
            embedding_models = []
            all_models = []
            
            for model in models:
                model_name = model.name
                all_models.append(model_name)
                
                # Check if model supports embedContent method
                if hasattr(model, 'supported_generation_methods'):
                    methods = model.supported_generation_methods
                    if 'embedContent' in methods:
                        embedding_models.append(model_name)
            
            print(f"📋 All Available Models ({len(all_models)}):")
            for model in all_models[:10]:  # Show first 10
                print(f"   {model}")
            if len(all_models) > 10:
                print(f"   ... and {len(all_models) - 10} more")
            
            print(f"\n🧠 Embedding-Capable Models ({len(embedding_models)}):")
            for model in embedding_models:
                print(f"   ✅ {model}")
            
            return embedding_models
            
        except Exception as e:
            print(f"❌ Failed to list models: {e}")
            return []
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks."""
        return self.text_splitter.split_documents(documents)
    
    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query with task_type optimization."""
        # Temporarily set task_type to retrieval_query for queries
        original_task_type = getattr(self.embeddings, 'task_type', None)
        if hasattr(self.embeddings, 'task_type'):
            self.embeddings.task_type = "retrieval_query"
        
        try:
            embedding = self.embeddings.embed_query(text)
            # Show actual dimensions vs expected
            if len(embedding) != self.output_dimensionality:
                print(f"ℹ️ Note: Model outputs {len(embedding)}D vectors (expected {self.output_dimensionality}D)")
            return embedding
        finally:
            # Restore original task_type
            if hasattr(self.embeddings, 'task_type') and original_task_type:
                self.embeddings.task_type = original_task_type
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple documents."""
        embeddings = self.embeddings.embed_documents(texts)
        # Show actual dimensions vs expected only once
        if embeddings and len(embeddings[0]) != self.output_dimensionality:
            print(f"ℹ️ Note: Model outputs {len(embeddings[0])}D vectors (expected {self.output_dimensionality}D)")
        return embeddings
    
    def get_embeddings_client(self):
        """Get the underlying LangChain embeddings client."""
        return self.embeddings
    
    def get_model_info(self) -> dict:
        """Get information about the current model configuration."""
        return {
            "model": self.model,
            "expected_dimensionality": self.output_dimensionality,
            "chunk_size": self.text_splitter._chunk_size,
            "chunk_overlap": self.text_splitter._chunk_overlap
        } 