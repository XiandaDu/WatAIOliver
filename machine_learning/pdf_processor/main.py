"""
Simple PDF to Markdown API

Minimal FastAPI service for converting PDFs to Markdown using Marker.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

from config import get_settings
from service.pdf_conversion_service import PDFConversionService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="PDF to Markdown Converter",
    description="Convert PDF documents to Markdown with high-quality formula preservation using Marker",
    version="1.0.0",
    docs_url="/docs"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instance
_pdf_service: Optional[PDFConversionService] = None


def get_pdf_service() -> PDFConversionService:
    """Get or create PDF conversion service instance."""
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = PDFConversionService(settings)
    return _pdf_service


# Response Model
class ConversionResponse(BaseModel):
    """Response model for PDF conversion."""
    success: bool
    markdown_content: str
    metadata: Dict[str, Any]
    processing_time: float
    error_message: Optional[str] = None
    filename: Optional[str] = None


# Endpoints
@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "PDF to Markdown Converter",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "PDF to Markdown Converter"}


@app.post("/convert", response_model=ConversionResponse)
async def convert_pdf_upload(file: UploadFile = File(...)):
    """
    Convert an uploaded PDF file to markdown format.
    Automatically saves the result to output/ directory.
    """
    try:
        # Validate file type
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Read file content
        pdf_bytes = await file.read()
        if len(pdf_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        logger.info(f"Converting PDF: {file.filename} ({len(pdf_bytes)/1024/1024:.1f}MB)")
        
        # Convert PDF (automatically saves to file)
        result = await get_pdf_service().convert_pdf_bytes(pdf_bytes, file.filename)
        
        # Prepare response
        return ConversionResponse(
            success=result.success,
            markdown_content=result.markdown_content,
            metadata=result.metadata,
            processing_time=result.processing_time,
            error_message=result.error_message,
            filename=file.filename
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"PDF conversion failed: {exc}")
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(exc)}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    ) 