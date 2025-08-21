"""
Universal Document Converter
Converts any input format (PDF, images, documents) to markdown using Gemini 2.0 Flash.
Fast, flexible solution for document processing.
"""

import os
import tempfile
import logging
import time
import asyncio
import aiofiles
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from pathlib import Path
import base64
from io import BytesIO

# Image processing
from PIL import Image
import fitz  # PyMuPDF for PDF to image conversion

# Google Gemini API
import google.generativeai as genai

# Load environment variables
from dotenv import load_dotenv
ml_env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(ml_env_path)

logger = logging.getLogger(__name__)

@dataclass
class ConversionResult:
    """Result of document conversion."""
    markdown_content: str
    metadata: Dict
    success: bool
    processing_time: float
    total_pages: int = 0
    error_message: Optional[str] = None

class UniversalDocumentConverter:
    """
    Universal document converter that handles any input format.
    Converts documents to images, then uses Gemini 2.5 Flash Lite for markdown conversion.
    """
    
    SYSTEM_PROMPT = """You are a professional document extractor. Your work is extract all the content of the inputted file. You are going to extract all the word in a nice formatting and make this file to be fully translated in to .md file. you will always output the file directly and only output the file without adding any comment of explanation.

# Very important: Whenever you detected the file is with diagrams, figures, or any other scenarios that the page is not completely structured with pure text, you will then have to manage to describe the content of this diagram or figure, to be displayed in a format [Diagram: xxx explaination]; No matter the position it is in the page, as detailed as possible."""

    SUPPORTED_IMAGE_FORMATS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}
    SUPPORTED_DOCUMENT_FORMATS = {'.pdf'}
    SUPPORTED_TEXT_FORMATS = {'.txt', '.md', '.mdx'}
    
    @classmethod
    def get_supported_formats_message(cls) -> str:
        """Get a user-friendly message listing all supported formats."""
        all_formats = cls.SUPPORTED_IMAGE_FORMATS | cls.SUPPORTED_DOCUMENT_FORMATS | cls.SUPPORTED_TEXT_FORMATS
        formats_list = sorted(list(all_formats))
        return f"Supported formats: {', '.join(formats_list)}"
    
    def __init__(self):
        """Initialize the converter with Gemini API."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
            
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('models/gemini-2.5-flash-lite')
        
        # Configure generation settings for thinking and quality
        self.generation_config = genai.types.GenerationConfig(
            temperature=0.1,  # Low temperature for consistency
            top_p=0.8,
            top_k=40,
            max_output_tokens=8192,
        )
        
        logger.info("UniversalDocumentConverter initialized with Gemini 2.5 Flash Lite")

    def _get_file_extension(self, filename: str) -> str:
        """Get file extension in lowercase."""
        return Path(filename).suffix.lower()

    def _is_image_file(self, filename: str) -> bool:
        """Check if file is a supported image format."""
        return self._get_file_extension(filename) in self.SUPPORTED_IMAGE_FORMATS

    def _is_pdf_file(self, filename: str) -> bool:
        """Check if file is a PDF."""
        return self._get_file_extension(filename) in self.SUPPORTED_DOCUMENT_FORMATS

    def _is_text_file(self, filename: str) -> bool:
        """Check if file is a supported text format."""
        return self._get_file_extension(filename) in self.SUPPORTED_TEXT_FORMATS

    async def _pdf_to_images(self, pdf_path: str) -> List[Image.Image]:
        """Convert PDF pages to PIL Images."""
        images = []
        try:
            pdf_document = fitz.open(pdf_path)
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                # Render page as image with high DPI for better quality
                pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))  # 2x scaling for better quality
                img_data = pix.tobytes("png")
                img = Image.open(BytesIO(img_data))
                images.append(img)
                logger.info(f"Converted PDF page {page_num + 1} to image")
            pdf_document.close()
        except Exception as e:
            logger.error(f"Error converting PDF to images: {e}")
            raise
        return images

    async def _load_image_file(self, file_path: str) -> Image.Image:
        """Load an image file."""
        try:
            img = Image.open(file_path)
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            return img
        except Exception as e:
            logger.error(f"Error loading image file: {e}")
            raise

    async def _load_text_file(self, file_path: str) -> str:
        """Load a text file and return its content."""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            return content
        except Exception as e:
            logger.error(f"Error loading text file: {e}")
            raise

    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string."""
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        img_bytes = buffer.getvalue()
        return base64.b64encode(img_bytes).decode('utf-8')

    async def _convert_image_to_markdown(self, image: Image.Image, page_number: int = None) -> str:
        """Convert a single image to markdown using Gemini."""
        try:
            # Convert image to base64 for Gemini
            img_base64 = self._image_to_base64(image)
            
            # Prepare the prompt
            prompt = self.SYSTEM_PROMPT
            if page_number is not None:
                prompt += f"\n\nThis is page {page_number} of the document."

            # Create the request
            response = await asyncio.to_thread(
                self.model.generate_content,
                [prompt, image],
                generation_config=self.generation_config
            )
            
            if response.text:
                logger.info(f"Successfully converted page {page_number or 'unknown'} to markdown")
                return response.text.strip()
            else:
                logger.warning(f"Empty response from Gemini for page {page_number or 'unknown'}")
                return ""
                
        except Exception as e:
            logger.error(f"Error converting image to markdown: {e}")
            # Don't include full error details in markdown output
            if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                return f"[Rate limit exceeded - page {page_number or 'unknown'} skipped]"
            else:
                return f"[Error processing page {page_number or 'unknown'}]"

    async def _process_images_to_markdown(self, images: List[Image.Image]) -> str:
        """Process multiple images to markdown and combine them."""
        markdown_parts = []
        
        # Process images with strict rate limiting for Gemini 2.5 Flash Lite (30 requests/min)
        # Use 1 concurrent request to stay well under rate limit
        semaphore = asyncio.Semaphore(1)  # Very conservative to avoid rate limits
        
        async def process_single_image(img: Image.Image, page_num: int) -> Tuple[int, str]:
            async with semaphore:
                # Add delay to respect rate limit: 30 requests/min = 1 request every 2 seconds
                if page_num > 0:  # Skip delay for first image
                    await asyncio.sleep(2.1)  # Slightly over 2 seconds to be safe
                result = await self._convert_image_to_markdown(img, page_num + 1)
                return page_num, result
        
        # Create tasks for all images
        tasks = [process_single_image(img, i) for i, img in enumerate(images)]
        
        # Execute all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Sort results by page number and combine
        valid_results = []
        for result in results:
            if isinstance(result, tuple):
                valid_results.append(result)
            else:
                logger.error(f"Task failed with exception: {result}")
        
        valid_results.sort(key=lambda x: x[0])  # Sort by page number
        
        for page_num, markdown in valid_results:
            if markdown.strip():
                if len(markdown_parts) > 0:
                    markdown_parts.append("\n\n---\n\n")  # Page separator
                markdown_parts.append(markdown)
        
        return "".join(markdown_parts)

    async def convert_file(self, file_path: str, filename: str = None) -> ConversionResult:
        """
        Convert any supported file format to markdown.
        
        Args:
            file_path: Path to the input file
            filename: Original filename (optional, used for metadata)
        
        Returns:
            ConversionResult with markdown content and metadata
        """
        start_time = time.time()
        
        if filename is None:
            filename = os.path.basename(file_path)
        
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                return ConversionResult(
                    markdown_content="",
                    metadata={"error": f"File not found: {file_path}"},
                    success=False,
                    processing_time=time.time() - start_time,
                    error_message=f"File not found: {file_path}"
                )

            logger.info(f"Converting file: {filename}")
            
            images = []
            
            # Handle different file types
            if self._is_pdf_file(filename):
                logger.info(f"Processing PDF: {filename}")
                images = await self._pdf_to_images(file_path)
            elif self._is_image_file(filename):
                logger.info(f"Processing image: {filename}")
                image = await self._load_image_file(file_path)
                images = [image]
            elif self._is_text_file(filename):
                logger.info(f"Processing text file: {filename}")
                # For text files, return the content directly without image processing
                text_content = await self._load_text_file(file_path)
                processing_time = time.time() - start_time
                
                metadata = {
                    "original_filename": filename,
                    "file_type": self._get_file_extension(filename),
                    "total_pages": 1,
                    "processing_time": processing_time,
                    "model_used": "direct_text"
                }
                
                logger.info(f"Text file processed in {processing_time:.2f}s")
                
                return ConversionResult(
                    markdown_content=text_content,
                    metadata=metadata,
                    success=True,
                    processing_time=processing_time,
                    total_pages=1
                )
            else:
                file_ext = self._get_file_extension(filename)
                error_msg = f"Sorry, unsupported file format '{file_ext}'. {self.get_supported_formats_message()}"
                return ConversionResult(
                    markdown_content="",
                    metadata={"error": error_msg, "unsupported_format": file_ext},
                    success=False,
                    processing_time=time.time() - start_time,
                    error_message=error_msg
                )

            if not images:
                return ConversionResult(
                    markdown_content="",
                    metadata={"error": "No images extracted from file"},
                    success=False,
                    processing_time=time.time() - start_time,
                    error_message="No images extracted from file"
                )

            # Convert images to markdown
            logger.info(f"Converting {len(images)} images to markdown using Gemini")
            markdown_content = await self._process_images_to_markdown(images)
            
            processing_time = time.time() - start_time
            
            metadata = {
                "original_filename": filename,
                "file_type": self._get_file_extension(filename),
                "total_pages": len(images),
                "processing_time": processing_time,
                "model_used": "gemini-2.5-flash-lite"
            }
            
            logger.info(f"Conversion completed in {processing_time:.2f}s")
            
            return ConversionResult(
                markdown_content=markdown_content,
                metadata=metadata,
                success=True,
                processing_time=processing_time,
                total_pages=len(images)
            )

        except Exception as e:
            error_msg = f"Conversion failed: {str(e)}"
            logger.error(error_msg)
            return ConversionResult(
                markdown_content="",
                metadata={"error": str(e), "original_filename": filename},
                success=False,
                processing_time=time.time() - start_time,
                error_message=error_msg
            )

    async def convert_bytes(self, file_bytes: bytes, filename: str) -> ConversionResult:
        """
        Convert file bytes to markdown.
        
        Args:
            file_bytes: Raw file bytes
            filename: Original filename (used to determine file type)
        
        Returns:
            ConversionResult with markdown content and metadata
        """
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=self._get_file_extension(filename), delete=False) as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name

        try:
            result = await self.convert_file(temp_path, filename)
            return result
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    async def save_markdown(self, markdown_content: str, filename: str, output_dir: str = "output") -> str:
        """
        Save markdown content to file.
        
        Args:
            markdown_content: The markdown content to save
            filename: Original filename
            output_dir: Output directory
        
        Returns:
            Path to saved file
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output filename
        base_name = Path(filename).stem
        output_path = os.path.join(output_dir, f"{base_name}.md")
        
        # Save the file
        async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
            await f.write(markdown_content)
        
        logger.info(f"Saved markdown to: {output_path}")
        return output_path