"""
Text Processing and Chunking Service

This module provides text preprocessing and chunking functionality for RAG applications.
It follows Google's recommended practices for text-embedding-004 and includes
adaptive chunking with proper buffer management.

Improvements over legacy system:
- Removes 200-word hard limit
- Adds semantic-aware chunking
- Implements proper preprocessing pipeline
- Provides configurable chunk overlap and buffer
"""

import re
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import unicodedata

logger = logging.getLogger(__name__)


@dataclass
class ChunkMetadata:
    """Metadata for text chunks"""
    source_id: str
    chunk_index: int
    total_chunks: int
    start_char: int
    end_char: int
    word_count: int
    char_count: int


@dataclass
class ChunkingConfig:
    """Configuration for text chunking"""
    max_chunk_size: int = 800  # Increased from legacy 200-word limit
    min_chunk_size: int = 100  # Minimum viable chunk size
    chunk_overlap: int = 150   # Overlap between chunks (buffer)
    target_chunk_size: int = 600  # Target size for adaptive chunking
    use_semantic_boundaries: bool = True  # Respect sentence/paragraph boundaries
    max_token_buffer: int = 50  # Buffer before hitting token limits


class TextPreprocessor:
    """
    Text preprocessing following Google's recommendations for text-embedding-004.
    
    Based on Google's documentation, preprocessing should normalize text while
    preserving semantic meaning and structure.
    """
    
    def __init__(self):
        self.sentence_endings = re.compile(r'[.!?]+\s+')
        self.paragraph_breaks = re.compile(r'\n\s*\n')
        self.whitespace_normalizer = re.compile(r'\s+')
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text following Google's recommendations.
        
        Args:
            text: Raw input text
            
        Returns:
            Preprocessed text ready for embedding
        """
        if not text or not text.strip():
            return ""
        
        # Step 1: Unicode normalization (Google recommendation)
        text = unicodedata.normalize('NFKC', text)
        
        # Step 2: Remove excessive whitespace but preserve structure
        text = self.whitespace_normalizer.sub(' ', text)
        
        # Step 3: Handle special characters and encoding issues
        text = self._clean_special_characters(text)
        
        # Step 4: Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Step 5: Remove excessive blank lines but preserve paragraph structure
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def _clean_special_characters(self, text: str) -> str:
        """Clean special characters while preserving semantic meaning"""
        # Replace common problematic characters
        replacements = {
            '"': '"',  # Smart quotes
            '"': '"',
            ''': "'",
            ''': "'",
            '–': '-',  # En dash
            '—': '-',  # Em dash
            '…': '...',  # Ellipsis
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def extract_structural_elements(self, text: str) -> Dict[str, List[int]]:
        """
        Extract structural elements for semantic-aware chunking.
        
        Returns:
            Dictionary with positions of sentences, paragraphs, etc.
        """
        elements = {
            'sentences': [],
            'paragraphs': [],
        }
        
        # Find sentence boundaries
        for match in self.sentence_endings.finditer(text):
            elements['sentences'].append(match.end())
        
        # Find paragraph boundaries
        for match in self.paragraph_breaks.finditer(text):
            elements['paragraphs'].append(match.end())
            
        return elements


class AdaptiveChunker:
    """
    Adaptive text chunker that respects semantic boundaries and provides
    configurable overlap for better RAG performance.
    
    Improvements over legacy 200-word limit:
    - Adaptive sizing based on content structure
    - Semantic boundary awareness
    - Configurable overlap and buffer
    - Better metadata tracking
    """
    
    def __init__(self, config: ChunkingConfig = None, preprocessor: TextPreprocessor = None):
        self.config = config or ChunkingConfig()
        self.preprocessor = preprocessor or TextPreprocessor()
        logger.info(f"Initialized AdaptiveChunker with max_chunk_size={self.config.max_chunk_size}")
    
    def chunk_text(self, text: str, source_id: str = "unknown") -> List[Tuple[str, ChunkMetadata]]:
        """
        Chunk text using adaptive strategy with semantic awareness.
        
        Args:
            text: Input text to chunk
            source_id: Identifier for the source document
            
        Returns:
            List of (chunk_text, metadata) tuples
        """
        if not text or not text.strip():
            return []
        
        # Preprocess the text
        processed_text = self.preprocessor.preprocess_text(text)
        
        if len(processed_text) <= self.config.max_chunk_size:
            # Text is small enough to be a single chunk
            metadata = ChunkMetadata(
                source_id=source_id,
                chunk_index=0,
                total_chunks=1,
                start_char=0,
                end_char=len(processed_text),
                word_count=len(processed_text.split()),
                char_count=len(processed_text)
            )
            return [(processed_text, metadata)]
        
        # Extract structural elements for semantic chunking
        if self.config.use_semantic_boundaries:
            return self._semantic_chunk(processed_text, source_id)
        else:
            return self._simple_chunk(processed_text, source_id)
    
    def _semantic_chunk(self, text: str, source_id: str) -> List[Tuple[str, ChunkMetadata]]:
        """Chunk text respecting semantic boundaries"""
        structural_elements = self.preprocessor.extract_structural_elements(text)
        chunks = []
        current_pos = 0
        chunk_index = 0
        
        while current_pos < len(text):
            chunk_end = self._find_optimal_chunk_end(
                text, current_pos, structural_elements
            )
            
            chunk_text = text[current_pos:chunk_end].strip()
            
            if chunk_text:  # Only add non-empty chunks
                metadata = ChunkMetadata(
                    source_id=source_id,
                    chunk_index=chunk_index,
                    total_chunks=0,  # Will update after all chunks are created
                    start_char=current_pos,
                    end_char=chunk_end,
                    word_count=len(chunk_text.split()),
                    char_count=len(chunk_text)
                )
                chunks.append((chunk_text, metadata))
                chunk_index += 1
            
            # Move to next position with overlap
            overlap_start = max(
                current_pos + self.config.target_chunk_size - self.config.chunk_overlap,
                chunk_end - self.config.chunk_overlap
            )
            current_pos = max(overlap_start, chunk_end)
        
        # Update total_chunks in metadata
        total_chunks = len(chunks)
        for chunk_text, metadata in chunks:
            metadata.total_chunks = total_chunks
        
        logger.info(f"Created {total_chunks} semantic chunks for {source_id}")
        return chunks
    
    def _find_optimal_chunk_end(
        self, 
        text: str, 
        start_pos: int, 
        structural_elements: Dict[str, List[int]]
    ) -> int:
        """Find the optimal end position for a chunk respecting semantic boundaries"""
        
        target_end = start_pos + self.config.target_chunk_size
        max_end = start_pos + self.config.max_chunk_size
        
        if target_end >= len(text):
            return len(text)
        
        # Try to end at a paragraph boundary first
        best_end = self._find_boundary_before(
            structural_elements['paragraphs'], target_end, start_pos + self.config.min_chunk_size
        )
        
        if best_end:
            return min(best_end, max_end)
        
        # Fall back to sentence boundary
        best_end = self._find_boundary_before(
            structural_elements['sentences'], target_end, start_pos + self.config.min_chunk_size
        )
        
        if best_end:
            return min(best_end, max_end)
        
        # Fall back to word boundary
        word_end = self._find_word_boundary(text, target_end)
        return min(word_end, max_end)
    
    def _find_boundary_before(self, boundaries: List[int], target_pos: int, min_pos: int) -> Optional[int]:
        """Find the best boundary position before target_pos but after min_pos"""
        valid_boundaries = [b for b in boundaries if min_pos <= b <= target_pos]
        return max(valid_boundaries) if valid_boundaries else None
    
    def _find_word_boundary(self, text: str, target_pos: int) -> int:
        """Find a word boundary near the target position"""
        if target_pos >= len(text):
            return len(text)
        
        # Look backwards for a space
        for i in range(target_pos, max(0, target_pos - 50), -1):
            if text[i].isspace():
                return i
        
        return target_pos
    
    def _simple_chunk(self, text: str, source_id: str) -> List[Tuple[str, ChunkMetadata]]:
        """Simple character-based chunking as fallback"""
        chunks = []
        current_pos = 0
        chunk_index = 0
        
        while current_pos < len(text):
            chunk_end = min(current_pos + self.config.max_chunk_size, len(text))
            chunk_text = text[current_pos:chunk_end]
            
            metadata = ChunkMetadata(
                source_id=source_id,
                chunk_index=chunk_index,
                total_chunks=0,
                start_char=current_pos,
                end_char=chunk_end,
                word_count=len(chunk_text.split()),
                char_count=len(chunk_text)
            )
            chunks.append((chunk_text, metadata))
            chunk_index += 1
            
            current_pos = chunk_end - self.config.chunk_overlap
        
        # Update total chunks
        total_chunks = len(chunks)
        for chunk_text, metadata in chunks:
            metadata.total_chunks = total_chunks
        
        return chunks


class TextProcessingService:
    """Main service for text processing and chunking"""
    
    def __init__(self, chunking_config: ChunkingConfig = None):
        self.preprocessor = TextPreprocessor()
        self.chunker = AdaptiveChunker(chunking_config, self.preprocessor)
    
    def process_document(self, text: str, source_id: str) -> List[Tuple[str, ChunkMetadata]]:
        """
        Process a document for RAG ingestion.
        
        Args:
            text: Raw document text
            source_id: Document identifier
            
        Returns:
            List of processed chunks with metadata
        """
        return self.chunker.chunk_text(text, source_id)
    
    def get_chunk_statistics(self, chunks: List[Tuple[str, ChunkMetadata]]) -> Dict:
        """Get statistics about the chunks"""
        if not chunks:
            return {}
        
        word_counts = [metadata.word_count for _, metadata in chunks]
        char_counts = [metadata.char_count for _, metadata in chunks]
        
        return {
            'total_chunks': len(chunks),
            'avg_word_count': sum(word_counts) / len(word_counts),
            'avg_char_count': sum(char_counts) / len(char_counts),
            'min_word_count': min(word_counts),
            'max_word_count': max(word_counts),
            'min_char_count': min(char_counts),
            'max_char_count': max(char_counts),
        } 