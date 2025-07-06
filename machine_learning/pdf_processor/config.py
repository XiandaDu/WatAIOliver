"""
Configuration for PDF Processor Service
"""
import os
from pydantic import BaseModel


class Settings(BaseModel):
    """Basic PDF Processor settings."""

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8001
    debug: bool = False


def get_settings() -> Settings:
    """Get settings from environment variables."""
    return Settings(
        host=os.getenv("PDF_HOST", "0.0.0.0"),
        port=int(os.getenv("PDF_PORT", "8001")),
        debug=os.getenv("PDF_DEBUG", "false").lower() == "true"
    ) 