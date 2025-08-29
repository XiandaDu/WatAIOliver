"""
Universal Document to Markdown API

FastAPI service for converting any document format (PDF, images, etc.) to Markdown using Gemini.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

from machine_learning.pdf_processor.config import get_settings
from machine_learning.pdf_processor.service.universal_document_converter import UniversalDocumentConverter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create FastAPI app with metadata
app = FastAPI(
    title="Universal Document to Markdown Converter",
    description="Convert any document format (PDF, images, etc.) to Markdown using Gemini AI",
    version="2.0.0",
    docs_url="/docs"
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instance
_converter_service: Optional[UniversalDocumentConverter] = None


def get_converter_service() -> UniversalDocumentConverter:
    """
    Get or create document conversion service instance.
    Ensures only one instance is used throughout the app.
    """
    global _converter_service
    if _converter_service is None:
        _converter_service = UniversalDocumentConverter()
    return _converter_service


# Response Model
class ConversionResponse(BaseModel):
    """Response model for document conversion."""
    success: bool
    markdown_content: str
    metadata: Dict[str, Any]
    processing_time: float
    total_pages: int
    error_message: Optional[str] = None
    filename: Optional[str] = None


# Endpoints
@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "Universal Document to Markdown Converter",
        "version": "2.0.0",
        "status": "running",
        "supported_formats": ["PDF", "PNG", "JPG", "JPEG", "GIF", "BMP", "TIFF", "WEBP", "TXT", "MD", "MDX"],
        "docs": "/docs"
    }


# Health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Universal Document to Markdown Converter"}


# Document conversion endpoint
@app.post("/convert", response_model=ConversionResponse)
async def convert_document_upload(file: UploadFile = File(...)):
    """
    Convert an uploaded document (PDF, image, etc.) to markdown format.
    Automatically saves the result to output/ directory.
    """
    try:
        # Validate file exists and has content
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Read file content
        file_bytes = await file.read()
        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        logger.info(f"Converting document: {file.filename} ({len(file_bytes)/1024/1024:.1f}MB)")
        
        # Convert document using universal converter
        result = await get_converter_service().convert_bytes(file_bytes, file.filename)
        
        # Save markdown to file if conversion succeeded
        if result.success and result.markdown_content:
            saved_path = await get_converter_service().save_markdown(
                result.markdown_content, 
                file.filename
            )
            result.metadata["saved_to"] = saved_path
            logger.info(f"Automatically saved to: {saved_path}")
        
        # Prepare and return API response
        return ConversionResponse(
            success=result.success,
            markdown_content=result.markdown_content,
            metadata=result.metadata,
            processing_time=result.processing_time,
            total_pages=result.total_pages,
            error_message=result.error_message,
            filename=file.filename
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Document conversion failed: {exc}")
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(exc)}")


# Run the app with Uvicorn if executed directly
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    ) 
