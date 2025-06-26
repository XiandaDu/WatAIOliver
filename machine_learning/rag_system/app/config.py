import os
from pathlib import Path
from pydantic import BaseModel

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv not installed, use system env vars


class Settings(BaseModel):
    """Application settings loaded from environment variables."""

    google_api_key: str = ""
    supabase_url: str = ""
    supabase_key: str = ""

def get_settings() -> Settings:
    return Settings(
        google_api_key=os.getenv("GOOGLE_API_KEY", ""),
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_key=os.getenv("SUPABASE_SERVICE_KEY", ""),
    )
