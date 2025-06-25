import os
from pydantic import BaseModel


class Settings(BaseModel):
    """Application settings loaded from environment variables."""

    gemini_api_key: str = ""
    supabase_url: str = ""
    supabase_key: str = ""

def get_settings() -> Settings:
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_key=os.getenv("SUPABASE_SERVICE_KEY", ""),
    )
