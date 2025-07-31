"""
WatAIOliver Machine Learning - Configuration Constants

This file contains ML-specific configuration parameters including
official model identifiers, processing parameters, and system limits.
"""

# =============================================================================
# MODEL CONFIGURATION
# =============================================================================

class ModelConfig:
    """LLM and embedding model configuration parameters"""

    # Model Parameters
    DEFAULT_TEMPERATURE = 0.1
    


    # Unified vector dimensionality across all embedding models
    EMBEDDING_DIMENSION = 512
    DEFAULT_OUTPUT_DIMENSIONALITY = EMBEDDING_DIMENSION
    LEGACY_OUTPUT_DIMENSIONALITY = EMBEDDING_DIMENSION
    OPENAI_SMALL_DIMENSIONALITY = EMBEDDING_DIMENSION
    OPENAI_LARGE_DIMENSIONALITY = EMBEDDING_DIMENSION

# =============================================================================
# TEXT PROCESSING CONFIGURATION
# =============================================================================

class TextProcessingConfig:
    """Text chunking and processing parameters"""
    
    # Chunking Parameters
    DEFAULT_CHUNK_SIZE = 800
    DEFAULT_CHUNK_OVERLAP = 150
    MAX_CHUNK_SIZE = 1000
    CHUNK_OVERLAP_RATIO = 0.1
    
    # Text Separators
    CHUNK_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]
    
    # Retrieval Settings
    DEFAULT_RETRIEVAL_K = 4
    DEFAULT_SCORE_THRESHOLD = 0.1
    FETCH_K_MULTIPLIER = 5  # fetch_k = k * 5
    
    # Context Limits
    MAX_CONVERSATION_LENGTH = 10
    MAX_BACKGROUND_TOKENS = 500
    MAX_CONTEXT_TOKENS = 1024