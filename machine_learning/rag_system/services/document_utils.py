"""
Document Processing Utilities

This module provides document processing utilities modernized from the legacy system.
It includes PDF processing, text extraction, and document management functions.

Improvements over legacy:
- Better error handling and logging
- Type hints and documentation
- Modern PDF processing
- Integration with new RAG pipeline
"""

import os
import re
import tempfile
import zipfile
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import shutil

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Enhanced document processor for various file types.
    
    Modernized from legacy system with better structure and error handling.
    """
    
    def __init__(self):
        self.supported_formats = {'.txt', '.md', '.pdf', '.docx'}
        logger.info("Initialized DocumentProcessor")
    
    def process_file(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Process a file and extract text content.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_path = Path(file_path)
        file_extension = file_path.suffix.lower()
        
        if file_extension not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_extension}")
        
        logger.info(f"Processing file: {file_path.name}")
        
        metadata = {
            'filename': file_path.name,
            'file_size': file_path.stat().st_size,
            'file_type': file_extension,
            'source_path': str(file_path)
        }
        
        try:
            if file_extension == '.txt':
                text = self._process_text_file(file_path)
            elif file_extension == '.md':
                text = self._process_markdown_file(file_path)
            elif file_extension == '.pdf':
                text = self._process_pdf_file(file_path)
            elif file_extension == '.docx':
                text = self._process_docx_file(file_path)
            else:
                raise ValueError(f"Handler not implemented for {file_extension}")
            
            metadata['word_count'] = len(text.split())
            metadata['char_count'] = len(text)
            metadata['success'] = True
            
            logger.info(f"Successfully processed {file_path.name}: {metadata['word_count']} words")
            return text, metadata
            
        except Exception as e:
            logger.error(f"Failed to process file {file_path.name}: {e}")
            metadata['error'] = str(e)
            metadata['success'] = False
            return "", metadata
    
    def _process_text_file(self, file_path: Path) -> str:
        """Process plain text file"""
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    
    def _process_markdown_file(self, file_path: Path) -> str:
        """Process Markdown file"""
        # For now, treat as plain text
        # Could be enhanced with markdown parsing later
        return self._process_text_file(file_path)
    
    def _process_pdf_file(self, file_path: Path) -> str:
        """
        Process PDF file to extract text.
        
        Note: This is a placeholder implementation.
        In production, you might want to use:
        - PyPDF2/PyMuPDF for basic text extraction
        - More advanced OCR for scanned PDFs
        - The PDF → Markdown converter discussed in the user context
        """
        try:
            # Try to import PDF processing library
            import PyPDF2
            
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            
            return text
            
        except ImportError:
            logger.warning("PyPDF2 not installed. Install with: pip install PyPDF2")
            raise ImportError("PDF processing requires PyPDF2. Please install it.")
        except Exception as e:
            logger.error(f"Failed to process PDF: {e}")
            raise
    
    def _process_docx_file(self, file_path: Path) -> str:
        """Process DOCX file"""
        try:
            # Try to import docx processing library
            from docx import Document
            
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text
            
        except ImportError:
            logger.warning("python-docx not installed. Install with: pip install python-docx")
            raise ImportError("DOCX processing requires python-docx. Please install it.")
        except Exception as e:
            logger.error(f"Failed to process DOCX: {e}")
            raise


class TextSplitter:
    """
    Enhanced text splitter modernized from legacy system.
    
    Provides regex-based text splitting with better error handling.
    """
    
    def __init__(self):
        logger.info("Initialized TextSplitter")
    
    def split_text_by_pattern(
        self, 
        text: str, 
        pattern: str, 
        keep_delimiter: bool = True
    ) -> List[str]:
        """
        Split text using a regex pattern.
        
        Args:
            text: Text to split
            pattern: Regex pattern for splitting
            keep_delimiter: Whether to keep the delimiter in results
            
        Returns:
            List of text segments
        """
        try:
            compiled_pattern = re.compile(pattern)
            
            if keep_delimiter:
                # Split but keep the delimiter
                parts = compiled_pattern.split(text)
                # Recombine with delimiters
                result = []
                for i in range(0, len(parts) - 1, 2):
                    if i + 1 < len(parts):
                        segment = parts[i] + parts[i + 1]
                        if segment.strip():
                            result.append(segment.strip())
                if parts and parts[-1].strip():
                    result.append(parts[-1].strip())
                return result
            else:
                return [part.strip() for part in compiled_pattern.split(text) if part.strip()]
        
        except re.error as e:
            logger.error(f"Invalid regex pattern: {e}")
            raise ValueError(f"Invalid regex pattern: {e}")
        except Exception as e:
            logger.error(f"Failed to split text: {e}")
            raise
    
    def split_by_sections(self, text: str) -> List[Dict[str, str]]:
        """
        Split text into sections based on headers.
        
        Returns:
            List of dictionaries with 'header' and 'content' keys
        """
        # Pattern for headers (lines starting with #, ##, etc. or all caps)
        header_pattern = r'^(#{1,6}\s+.*|[A-Z][A-Z\s]+)$'
        
        lines = text.split('\n')
        sections = []
        current_header = "Introduction"
        current_content = []
        
        for line in lines:
            if re.match(header_pattern, line.strip()):
                # Save previous section
                if current_content:
                    sections.append({
                        'header': current_header,
                        'content': '\n'.join(current_content).strip()
                    })
                
                # Start new section
                current_header = line.strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Add final section
        if current_content:
            sections.append({
                'header': current_header,
                'content': '\n'.join(current_content).strip()
            })
        
        return sections


class ZipProcessor:
    """
    Enhanced ZIP file processor modernized from legacy system.
    
    Handles ZIP files containing documents for batch processing.
    """
    
    def __init__(self, document_processor: DocumentProcessor = None):
        self.document_processor = document_processor or DocumentProcessor()
        logger.info("Initialized ZipProcessor")
    
    def process_zip_file(self, zip_path: str, extract_to: str = None) -> List[Dict[str, Any]]:
        """
        Process all supported files in a ZIP archive.
        
        Args:
            zip_path: Path to ZIP file
            extract_to: Directory to extract to (uses temp dir if None)
            
        Returns:
            List of processing results for each file
        """
        if not os.path.exists(zip_path):
            raise FileNotFoundError(f"ZIP file not found: {zip_path}")
        
        if extract_to is None:
            extract_to = tempfile.mkdtemp(prefix='zip_processing_')
            cleanup_temp = True
        else:
            cleanup_temp = False
            os.makedirs(extract_to, exist_ok=True)
        
        results = []
        
        try:
            logger.info(f"Processing ZIP file: {zip_path}")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Extract all files
                zip_ref.extractall(extract_to)
                
                # Get list of extracted files
                extracted_files = []
                for root, dirs, files in os.walk(extract_to):
                    for file in files:
                        file_path = os.path.join(root, file)
                        extracted_files.append(file_path)
                
                # Process each supported file
                for file_path in extracted_files:
                    try:
                        file_ext = Path(file_path).suffix.lower()
                        if file_ext in self.document_processor.supported_formats:
                            text, metadata = self.document_processor.process_file(file_path)
                            
                            result = {
                                'file_path': file_path,
                                'relative_path': os.path.relpath(file_path, extract_to),
                                'text': text,
                                'metadata': metadata
                            }
                            results.append(result)
                        else:
                            logger.debug(f"Skipping unsupported file: {file_path}")
                    
                    except Exception as e:
                        logger.error(f"Failed to process file {file_path}: {e}")
                        results.append({
                            'file_path': file_path,
                            'relative_path': os.path.relpath(file_path, extract_to),
                            'text': "",
                            'metadata': {'error': str(e), 'success': False}
                        })
            
            logger.info(f"Processed ZIP file: {len(results)} files")
            return results
            
        except Exception as e:
            logger.error(f"Failed to process ZIP file: {e}")
            raise
        
        finally:
            # Cleanup temporary directory if we created it
            if cleanup_temp:
                shutil.rmtree(extract_to, ignore_errors=True)


class LegacyMigrationHelper:
    """
    Helper class for migrating data from legacy Oliver system.
    
    Provides utilities to convert legacy data formats to new system.
    """
    
    def __init__(self):
        logger.info("Initialized LegacyMigrationHelper")
    
    def convert_legacy_chunks(self, legacy_chunks: List[str], source_id: str) -> List[Dict[str, Any]]:
        """
        Convert legacy chunk format to new enhanced format.
        
        Args:
            legacy_chunks: List of legacy text chunks
            source_id: Source document identifier
            
        Returns:
            List of enhanced chunk dictionaries
        """
        converted_chunks = []
        
        for i, chunk_text in enumerate(legacy_chunks):
            if not chunk_text or not chunk_text.strip():
                continue
                
            enhanced_chunk = {
                'text': chunk_text.strip(),
                'metadata': {
                    'source_id': source_id,
                    'chunk_index': i,
                    'total_chunks': len(legacy_chunks),
                    'word_count': len(chunk_text.split()),
                    'char_count': len(chunk_text),
                    'migrated_from_legacy': True,
                    'original_chunking_method': 'legacy_200_word_limit'
                }
            }
            converted_chunks.append(enhanced_chunk)
        
        logger.info(f"Converted {len(converted_chunks)} legacy chunks for {source_id}")
        return converted_chunks
    
    def estimate_rechunking_improvement(self, legacy_chunks: List[str]) -> Dict[str, Any]:
        """
        Estimate the improvement from rechunking legacy data.
        
        Args:
            legacy_chunks: List of legacy chunks
            
        Returns:
            Dictionary with improvement estimates
        """
        if not legacy_chunks:
            return {}
        
        word_counts = [len(chunk.split()) for chunk in legacy_chunks]
        char_counts = [len(chunk) for chunk in legacy_chunks]
        
        # Estimate new chunking (semantic boundaries, better overlap)
        total_text = " ".join(legacy_chunks)
        estimated_new_chunks = len(total_text) // 600  # New target chunk size
        estimated_new_chunks = max(1, estimated_new_chunks)
        
        improvement_estimate = {
            'legacy_stats': {
                'total_chunks': len(legacy_chunks),
                'avg_word_count': sum(word_counts) / len(word_counts),
                'avg_char_count': sum(char_counts) / len(char_counts),
                'chunking_method': '200-word hard limit'
            },
            'estimated_new_stats': {
                'estimated_chunks': estimated_new_chunks,
                'estimated_avg_char_count': 600,  # Target size
                'estimated_overlap': 150,  # Character overlap
                'chunking_method': 'semantic adaptive'
            },
            'improvement_summary': {
                'chunk_reduction': len(legacy_chunks) - estimated_new_chunks,
                'better_boundaries': True,
                'enhanced_metadata': True,
                'improved_embedding_model': 'text-embedding-004 (768D)'
            }
        }
        
        return improvement_estimate


# Utility functions for common document operations
def generate_document_id(filename: str, content_hash: Optional[str] = None) -> str:
    """Generate a unique document ID"""
    import hashlib
    
    if content_hash is None:
        content_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
    
    # Clean filename for use in ID
    clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', filename)
    return f"{clean_name}_{content_hash}"


def validate_document_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and clean document metadata"""
    required_fields = ['filename', 'file_type']
    
    for field in required_fields:
        if field not in metadata:
            logger.warning(f"Missing required metadata field: {field}")
    
    # Ensure numeric fields are properly typed
    for field in ['word_count', 'char_count', 'file_size']:
        if field in metadata and not isinstance(metadata[field], (int, float)):
            try:
                metadata[field] = int(metadata[field])
            except (ValueError, TypeError):
                logger.warning(f"Invalid {field} value: {metadata[field]}")
                metadata[field] = 0
    
    return metadata 