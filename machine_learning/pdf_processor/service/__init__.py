"""
PDF Processor Services
Simple PDF conversion service using official Marker pattern.
"""
# Import main service and result dataclass for external use
from .pdf_conversion_service import (
    PDFConversionService,
    ConversionResult
)

# Define public API for the service module
__all__ = [
    "PDFConversionService",
    "ConversionResult"
]