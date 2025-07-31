"""Configuration settings for the RAG system."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from machine_learning.constants import ModelConfig

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv not installed, use system env vars


class Settings(BaseSettings):
    """Application settings."""
    
    # Google API configuration
    google_api_key: str = ""  # Make this optional since we're using service account
    google_cloud_project: str  # Required for Vertex AI - must be set in environment
    google_cloud_location: str = "global"

    # Cerebras configuration
    cerebras_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_provider: str = "gemini"
    
    # Supabase configuration 
    supabase_url: str = ""
    supabase_api_key: str = ""  # Will be read from SUPABASE_SERVICE_KEY

    # Embedding model configuration
    embedding_model: str = "text-embedding-004"
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Allow extra fields from .env file
        
    def __init__(self, **kwargs):
        # Initialize settings and set Vertex AI environment var
        super().__init__(**kwargs)
        # Set Vertex AI environment var as per Google documentation
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"


def get_settings() -> Settings:
    """
    Function to create Settings instance with environment vars.
    """
    return Settings(
        google_api_key=os.getenv("GOOGLE_API_KEY", os.getenv("GEMINI_API_KEY", "")),  # use GEMINI_API_KEY as fallback for Gemini client
        google_cloud_project=os.getenv("GOOGLE_CLOUD_PROJECT", ""),  # Must be set for Vertex AI
        google_cloud_location=os.getenv("GOOGLE_CLOUD_LOCATION", "global"),
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_api_key=os.getenv("SUPABASE_SERVICE_KEY", ""),
        embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-004"),
        cerebras_api_key=os.getenv("CEREBRAS_API_KEY", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        llm_provider=os.getenv("LLM_PROVIDER", "gemini"),
    )

# Settings instance will be created when needed with proper environment variables
