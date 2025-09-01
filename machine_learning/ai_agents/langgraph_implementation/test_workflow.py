"""
Test script for LangGraph Multi-Agent Workflow

Demonstrates usage and tests the complete system.
"""

import asyncio
import logging
from typing import Dict, Any

from workflow import create_workflow
from state import AgentContext


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_workflow")


class MockLLMClient:
    """Mock LLM client for testing"""
    
    async def arun(self, **kwargs):
        """Mock LLM response"""
        return "Mock response for testing"
    
    def run(self, **kwargs):
        """Sync mock response"""
        return "Mock response for testing"


class MockRAGService:
    """Mock RAG service for testing"""
    
    async def retrieve(self, query: str, course_id: str, k: int = 5):
        """Mock retrieval"""
        return {
            "sources": [
                {
                    "content": f"Mock content about {query}",
                    "score": 0.9,
                    "source": "mock_document.pdf",
                    "metadata": {"page": 1}
                }
                for i in range(k)
            ]
        }


class MockConfig:
    """Mock configuration"""
    retrieval_k = 5
    max_debate_rounds = 3
    enable_debug_logging = True
    strategist_temperature = 0.7
    critic_temperature = 0.3


async def test_basic_workflow():
    """Test basic workflow execution"""
    
    logger.info("="*80)
    logger.info("TESTING BASIC WORKFLOW")
    logger.info("="*80)
    
    # Create mock dependencies
    llm_client = MockLLMClient()
    rag_service = MockRAGService()
    config = MockConfig()
    
    # Create workflow
    workflow = create_workflow(
        llm_client=llm_client,
        rag_service=rag_service,
        config=config,
        logger=logger
    )
    
    # Test query
    query = "Explain the concept of Lagrange multipliers in optimization"
    course_id = "test_course_001"
    session_id = "test_session_001"
    
    # Process query
    try:
        async for event in workflow.process_query(
            query=query,
            course_id=course_id,
            session_id=session_id,
            metadata={"test": True},
            max_rounds=2
        ):
            logger.info(f"Event: {event['status']} - {event.get('stage', '')}")
            
            if event["status"] == "complete":
                response = event["response"]
                logger.info("\nFINAL RESPONSE:")
                logger.info(f"  Success: {response['success']}")
                logger.info(f"  Answer keys: {list(response['answer'].keys())}")
                logger.info(f"  Metadata: {response['metadata']}")
                
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")


async def test_streaming_updates():
    """Test streaming updates during processing"""
    
    logger.info("="*80)
    logger.info("TESTING STREAMING UPDATES")
    logger.info("="*80)
    
    # Create workflow with real-time logging
    llm_client = MockLLMClient()
    rag_service = MockRAGService()
    config = MockConfig()
    
    workflow = create_workflow(
        llm_client=llm_client,
        rag_service=rag_service,
        config=config,
        logger=logger
    )
    
    query = "What is gradient descent?"
    updates = []
    
    async for event in workflow.process_query(
        query=query,
        course_id="test_course",
        session_id="test_stream"
    ):
        updates.append(event)
        if event["status"] == "in_progress":
            logger.info(f"  Progress: {event['stage']} - {event['message']}")
    
    logger.info(f"\nTotal updates received: {len(updates)}")


async def test_error_handling():
    """Test error handling in workflow"""
    
    logger.info("="*80)
    logger.info("TESTING ERROR HANDLING")
    logger.info("="*80)
    
    class ErrorLLMClient:
        async def arun(self, **kwargs):
            raise ValueError("Simulated LLM error")
    
    # Create workflow with error-prone client
    workflow = create_workflow(
        llm_client=ErrorLLMClient(),
        rag_service=MockRAGService(),
        config=MockConfig(),
        logger=logger
    )
    
    try:
        async for event in workflow.process_query(
            query="Test error handling",
            course_id="test_course",
            session_id="test_error"
        ):
            if event["status"] == "error":
                logger.info(f"Error caught: {event['error']}")
                break
    except Exception as e:
        logger.info(f"Exception handled: {str(e)}")


async def main():
    """Run all tests"""
    
    logger.info("STARTING LANGGRAPH WORKFLOW TESTS")
    logger.info("")
    
    # Run tests
    await test_basic_workflow()
    logger.info("")
    
    await test_streaming_updates()
    logger.info("")
    
    await test_error_handling()
    logger.info("")
    
    logger.info("ALL TESTS COMPLETED")


if __name__ == "__main__":
    asyncio.run(main())
