"""
Simple PDF to Markdown Conversion Service
Uses the official Marker pattern for high-quality PDF conversion.
"""

import os
import tempfile
import logging
import time
from typing import Dict, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

from config import Settings

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Official Marker imports
try:
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.output import text_from_rendered
    from marker.config.parser import ConfigParser
    MARKER_AVAILABLE = True
    logger.info("✅ Marker loaded successfully")
except ImportError as e:
    MARKER_AVAILABLE = False
    logger.error(f"❌ Marker not available: {e}")


@dataclass
class ConversionResult:
    """Result of PDF conversion."""
    markdown_content: str
    metadata: Dict
    images: Dict[str, bytes]
    success: bool
    processing_time: float
    error_message: Optional[str] = None


class PDFConversionService:
    """
    Simple PDF to Markdown conversion service using official Marker pattern.
    """

    def __init__(self, settings: Settings):
        """
        Initialize the PDFConversionService with provided settings.
        Raises RuntimeError if Marker is not available.
        """
        self.settings = settings
        self.logger = logging.getLogger(__name__)

        if not MARKER_AVAILABLE:
            raise RuntimeError("Marker is required but not available. Please install marker-pdf.")

    async def convert_pdf_to_markdown(self, pdf_path: str) -> ConversionResult:
        """
        Convert a PDF file to markdown using the official Marker pattern.
        Returns a ConversionResult dataclass.
        """
        start_time = time.time()

        try:
            # Validate input PDF path
            if not os.path.exists(pdf_path):
                return ConversionResult(
                    markdown_content="",
                    metadata={},
                    images={},
                    success=False,
                    processing_time=time.time() - start_time,
                    error_message=f"PDF file not found: {pdf_path}"
                )

            self.logger.info(f"🔄 Converting PDF: {pdf_path}")

            # Official Marker pattern with accuracy-first configuration from README
            # Force MPS for Apple Silicon GPU acceleration
            os.environ['TORCH_DEVICE'] = 'mps'

            # Load Gemini API key for LLM if available
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                self.logger.info(f"🤖 LLM enabled with API key: {api_key[:10]}...")
            else:
                self.logger.warning("⚠️ No GEMINI_API_KEY found, LLM disabled")

            # Maximum accuracy configuration from Marker README
            accuracy_config = {
                "format_lines": True,        # High-quality math output (from README)
                "redo_inline_math": True,    # Highest quality inline math (from README)
                "use_llm": bool(api_key),    # Only use LLM if API key is available
                "output_format": "markdown", # Explicit output format
            }

            # Add API key only if available
            if api_key:
                accuracy_config["gemini_api_key"] = api_key

            self.logger.info(f"📋 Config: {accuracy_config}")
            config_parser = ConfigParser(accuracy_config)

            # Create PDF converter with parsed config
            converter = PdfConverter(
                config=config_parser.generate_config_dict(),
                artifact_dict=create_model_dict(),
                processor_list=config_parser.get_processors(),
                renderer=config_parser.get_renderer(),
                llm_service=config_parser.get_llm_service()
            )
            # Perform conversion
            rendered = converter(pdf_path)
            text, metadata, images = text_from_rendered(rendered)

            processing_time = time.time() - start_time
            self.logger.info(f"✅ Conversion completed in {processing_time:.2f}s")

            return ConversionResult(
                markdown_content=text or "",
                metadata=metadata or {},
                images=images or {},
                success=True,
                processing_time=processing_time
            )

        except Exception as e:
            # Handle conversion errors and log them
            error_msg = f"Conversion failed: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            return ConversionResult(
                markdown_content="",
                metadata={"error": str(e)},
                images={},
                success=False,
                processing_time=time.time() - start_time,
                error_message=error_msg
            )

    async def convert_pdf_bytes(self, pdf_bytes: bytes, filename: str = "document.pdf") -> ConversionResult:
        """
        Convert PDF bytes to markdown format.
        Saves the markdown file if conversion is successful.
        Cleans up temporary PDF file after processing.
        """
        # Create temporary file for PDF bytes
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(pdf_bytes)
            temp_path = temp_file.name

        try:
            result = await self.convert_pdf_to_markdown(temp_path)

            # Fix metadata if it's not a dict
            if not isinstance(result.metadata, dict):
                result.metadata = {}
            result.metadata["original_filename"] = filename

            # Save markdown to file if conversion succeeded
            if result.success and result.markdown_content:
                saved_path = await self.save_markdown(result.markdown_content, filename)
                result.metadata["saved_to"] = saved_path
                self.logger.info(f"📁 Automatically saved to: {saved_path}")

            return result
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    async def save_markdown(self, markdown_content: str, filename: str, output_dir: str = "output") -> str:
        """
        Save markdown content to file in the specified output directory.
        Returns the path to the saved file.
        """
        import aiofiles

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Generate output filename
        base_name = filename.replace('.pdf', '').replace('.PDF', '')
        output_path = os.path.join(output_dir, f"{base_name}.md")

        # Save the file
        async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
            await f.write(markdown_content)

        self.logger.info(f"💾 Saved markdown to: {output_path}")
        return output_path 
