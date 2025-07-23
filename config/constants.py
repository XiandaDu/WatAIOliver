"""
WatAIOliver - Configuration Constants

This file contains magical values and configuration parameters that require
centralized management for consistency across the codebase.
"""

# =============================================================================
# SERVICE CONFIGURATION
# =============================================================================

class ServiceConfig:
    """Service URLs and port configuration"""
    
    # Service Ports
    FRONTEND_PORT = 5173
    BACKEND_PORT = 8000
    PDF_PROCESSOR_PORT = 8001
    RAG_SYSTEM_PORT = 8002
    AGENTS_SYSTEM_PORT = 8003
    
    # Service Hosts
    DEFAULT_HOST = "0.0.0.0"
    LOCALHOST = "localhost"
    
    # External Services
    NEBULA_BASE_URL = "http://ece-nebula07.eng.uwaterloo.ca:8976"
    
    # Test User
    TEST_USER_ID = "A1"
    TEST_USER_EMAIL = "test@test.com"
    TEST_USERNAME = "testuser"

# =============================================================================
# MODEL CONFIGURATION
# =============================================================================

class ModelConfig:
    """LLM and embedding model configuration parameters"""
    
    # Model Parameters
    DEFAULT_TEMPERATURE = 0.1
    DEFAULT_OUTPUT_DIMENSIONALITY = 512

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

# =============================================================================
# TIMEOUT CONFIGURATION
# =============================================================================

class TimeoutConfig:
    """Timeout settings for various operations"""
    
    # HTTP Request Timeouts (seconds)
    CHAT_REQUEST_TIMEOUT = 600  # 10 minutes to match agent system needs
    RAG_QUERY_TIMEOUT = 600  # 10 minutes for agent system with multiple LLM calls
    PDF_PROCESSING_TIMEOUT = 300  # 5 minutes
    RAG_PROCESSING_TIMEOUT = 120  # 2 minutes
    FILE_UPLOAD_TIMEOUT = 300     # 5 minutes
    
    # Database Operation Timeouts
    DB_QUERY_TIMEOUT = 30
    VECTOR_SEARCH_TIMEOUT = 10

# =============================================================================
# ERROR MESSAGES
# =============================================================================

class ErrorMessages:
    """Standardized error messages for user-facing responses"""
    
    # Agent System Errors
    AGENTS_SYSTEM_UNAVAILABLE = "The Agent System is currently unavailable. Please try again later or contact support."
    AGENTS_SYSTEM_ERROR = "The Agent System encountered an error while processing your request."
    AGENTS_COURSE_REQUIRED = "Agent System requires a course selection to identify the knowledge base."
    
    # Connection Errors
    CONNECTION_TIMEOUT = "Request timed out. The system is processing complex queries and may need more time."
    SERVICE_UNAVAILABLE = "Service temporarily unavailable. Please try again in a few moments."
    
    # General Errors
    UNKNOWN_ERROR = "An unexpected error occurred. Please try again or contact support." 