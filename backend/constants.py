"""
WatAIOliver Backend - Configuration Constants

This file contains backend-specific configuration parameters.
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