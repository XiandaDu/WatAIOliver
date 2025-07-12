"""
Configuration for PDF Processor Service
"""
import os
from pydantic import BaseModel

# Settings model for PDF Processor configuration
class Settings(BaseModel):
    """Basic PDF Processor settings."""

    # Server settings
    host: str = "0.0.0.0"  # Host address for the API server
    port: int = 8001        # Port for the API server
    debug: bool = False     # Debug mode flag


def get_settings() -> Settings:
    """
    Get settings from environment variables.
    Reads PDF_HOST, PDF_PORT, PDF_DEBUG from environment, falls back to defaults if vals not specified.
    """
    return Settings(
        host=os.getenv("PDF_HOST", "0.0.0.0"),
        port=int(os.getenv("PDF_PORT", "8001")),
        debug=os.getenv("PDF_DEBUG", "false").lower() == "true"
    ) 