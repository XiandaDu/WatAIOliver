"""Configuration settings for the RAG system."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings

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
    
    # Supabase configuration 
    supabase_url: str = ""
    supabase_api_key: str = ""  # Will be read from SUPABASE_SERVICE_KEY
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Allow extra fields from .env file
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set Vertex AI environment variable as per Google documentation
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"


def get_settings() -> Settings:
    return Settings(
        google_api_key=os.getenv("GOOGLE_API_KEY", ""),
        google_cloud_project=os.getenv("GOOGLE_CLOUD_PROJECT", ""),  # Must be set for Vertex AI
        google_cloud_location=os.getenv("GOOGLE_CLOUD_LOCATION", "global"),
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_api_key=os.getenv("SUPABASE_SERVICE_KEY", ""),
    )

# Settings instance will be created when needed with proper environment variables
