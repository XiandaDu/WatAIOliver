"""
Universal Document Processor Services
Universal document conversion service using Gemini AI.
"""
# Import main service and result dataclass for external use
from .universal_document_converter import (
    UniversalDocumentConverter,
    ConversionResult
)

# Define public API for the service module
__all__ = [
    "UniversalDocumentConverter",
    "ConversionResult"
]