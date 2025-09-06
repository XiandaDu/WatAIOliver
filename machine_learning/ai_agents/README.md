# LangGraph Multi-Agent System

A fully LangChain/LangGraph integrated implementation of the Speculative AI Multi-Agent System.

## Overview

This implementation replaces Python base classes with LangChain abstractions and uses LangGraph for workflow orchestration. It maintains all the original functionality including:

- Enhanced retrieval with speculative query reframing
- Multi-round debate loop with convergence control
- Critical verification and fact-checking
- Pedagogical tutoring and interaction management
- Comprehensive logging and monitoring

## Architecture

### Core Components

1. **LangGraph Workflow** (`workflow.py`)
   - StateGraph-based orchestration
   - Conditional routing between agents
   - Memory-backed conversation tracking
   - Real-time streaming updates

2. **LangChain Agents** (`agents/`)
   - **RetrieveAgent**: Enhanced RAG with speculative reframing using LangChain chains
   - **StrategistAgent**: Draft generation with structured output parsing
   - **CriticAgent**: Multi-chain verification (logic, facts, hallucinations)
   - **ModeratorAgent**: Decision chains with rule-based overrides
   - **ReporterAgent**: Synthesis chains for different debate outcomes
   - **TutorAgent**: Interactive learning with pattern detection

3. **State Management** (`state.py`)
   - Centralized WorkflowState for all agents
   - AgentContext for service injection
   - Comprehensive execution tracking

4. **FastAPI Service** (`service.py`)
   - REST API endpoints
   - Server-Sent Events streaming
   - Session management
   - Detailed logging

## Key Features

### LangChain Integration

- **Chains**: Each agent uses specialized LLMChains with custom prompts
- **Output Parsers**: Pydantic models for structured outputs
- **Tools**: Extensible tool framework for verification tasks
- **Prompts**: ChatPromptTemplate for consistent messaging

### LangGraph Benefits

- **Visual Workflow**: Clear graph structure with nodes and edges
- **State Management**: Automatic state passing between agents
- **Checkpointing**: Built-in conversation memory
- **Streaming**: Native support for real-time updates
- **Error Handling**: Graceful failure with state preservation

### Preserved Functionality

- All original logging with enhanced formatting
- Helper functions for RAG queries (`_perform_rag_query`)
- Speculative reframing logic
- Quality assessment algorithms
- Debate convergence rules
- Course-specific prompts

## Usage

### Basic Example

```python
from langgraph_implementation import create_workflow

# Initialize with your services
workflow = create_workflow(
    llm_client=your_llm_client,
    rag_service=your_rag_service,
    config=your_config,
    logger=your_logger
)

# Process a query
async for event in workflow.process_query(
    query="Explain Lagrange multipliers",
    course_id="math_101",
    session_id="user_session_123"
):
    if event["status"] == "complete":
        print(event["response"])
```

### FastAPI Service

```bash
# Start the service
python -m langgraph_implementation.service

# Make a request
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is gradient descent?",
    "course_id": "ml_course",
    "session_id": "session_001"
  }'
```

### Streaming Updates

```python
# Stream processing updates
async for event in workflow.process_query(...):
    if event["status"] == "in_progress":
        print(f"Processing: {event['stage']}")
```

## Configuration

The system uses the same configuration as the original:

```python
class SpeculativeAIConfig:
    max_debate_rounds = 3
    retrieval_k = 10
    enable_debug_logging = True
    strategist_temperature = 0.7
    critic_temperature = 0.3
```

## Logging

Comprehensive logging is maintained with:

- Agent execution tracking
- Processing time measurements
- Conversation history
- Error messages
- Debug information

Logs are written to both file and console with detailed formatting.

## Testing

Run the test suite:

```bash
python langgraph_implementation/test_workflow.py
```

Tests cover:
- Basic workflow execution
- Streaming updates
- Error handling
- Mock services

## Migration from Base Implementation

To migrate from the Python base class implementation:

1. Replace orchestrator import:
   ```python
   # Old
   from ai_agents.orchestrator import MultiAgentOrchestrator
   
   # New
   from langgraph_implementation import create_workflow
   ```

2. Update initialization:
   ```python
   # Old
   orchestrator = MultiAgentOrchestrator(config, rag_service, llm_client)
   
   # New
   workflow = create_workflow(llm_client, rag_service, config)
   ```

3. Update query processing:
   ```python
   # Old
   async for result in orchestrator.process_query(...):
       ...
   
   # New
   async for event in workflow.process_query(...):
       if event["status"] == "complete":
           result = event["response"]
   ```

## Advantages Over Base Implementation

1. **No Custom Base Classes**: Pure LangChain abstractions
2. **Visual Workflow**: Graph-based flow is easier to understand
3. **Better State Management**: LangGraph handles state automatically
4. **Native Streaming**: Built-in support for real-time updates
5. **Checkpointing**: Automatic conversation persistence
6. **Extensibility**: Easy to add new agents or modify flow
7. **Tool Integration**: Native LangChain tool support
8. **Error Recovery**: Better error handling with state preservation

## Requirements

```
langchain>=0.1.0
langgraph>=0.0.20
langchain-core>=0.1.0
langchain-community>=0.0.20
fastapi>=0.100.0
pydantic>=2.0.0
```

## Future Enhancements

- Add more LangChain tools for verification
- Implement LangSmith tracing
- Add vector store alternatives (Pinecone, Weaviate)
- Implement caching with Redis
- Add more sophisticated model routing
- Implement A/B testing for prompts
