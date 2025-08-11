# Speculative AI Multi-Agent System

A sophisticated multi-agent reasoning system that enhances traditional RAG with debate-based verification and iterative improvement.

## Architecture Overview

The system consists of 5 specialized agents working in concert:

1. **Retrieve Agent** - Speculative retriever with query reframing
2. **Strategist Agent** - Draft solution generator with Chain-of-Thought reasoning  
3. **Critic Agent** - Critical verification and issue identification
4. **Moderator Agent** - Debate flow control and convergence decisions
5. **Reporter Agent** - Final answer synthesis and formatting

## Key Features

- **Speculative Query Reframing** - Automatically generates alternative queries when initial retrieval quality is poor
- **Multi-Round Debate Process** - Iterative improvement through critic feedback
- **Convergence Detection** - Intelligent stopping criteria based on critique severity
- **Transparent Quality Assessment** - Clear indicators of verification level and confidence
- **Educational Formatting** - Structured answers optimized for learning

## Usage

### Via REST API

```bash
# Start the service (included in main setup.sh)
cd machine_learning/speculative_ai
uvicorn app.main:app --reload --host 0.0.0.0 --port 8003

# Query the system
curl -X POST "http://localhost:8003/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain Lagrange multipliers in optimization",
    "course_id": "math_optimization",
    "session_id": "demo_session"
  }'
```

### Via Backend Integration

The system is integrated with the main backend. Select "speculative" as the model in the chat interface.

```python
# In chat interface, the system is called automatically when:
data = ChatRequest(
    prompt="Your question here",
    model="speculative",  # Key parameter
    course_id="your_course_id"
)
```

## Configuration

Key configuration options in `SpeculativeAIConfig`:

```python
config = SpeculativeAIConfig(
    max_debate_rounds=3,           # Maximum iteration rounds
    retrieval_k=10,                # Initial retrieval count
    speculation_rounds=3,          # Alternative query generation
    convergence_threshold=0.7,     # Quality threshold for convergence
    enable_debug_logging=True      # Detailed debug information
)
```

## Response Format

### Standard Response (Converged)
```json
{
  "success": true,
  "answer": {
    "introduction": "Brief context-setting introduction",
    "step_by_step_solution": "Detailed solution with reasoning",
    "key_takeaways": "Important concepts and insights",
    "important_notes": "Limitations and considerations",
    "confidence_score": 0.95,
    "sources": ["source1.pdf", "source2.pdf"],
    "quality_indicators": {
      "debate_status": "converged",
      "verification_level": "high",
      "context_support": "strong"
    }
  },
  "metadata": {
    "debate_rounds": 2,
    "convergence_score": 0.95,
    "processing_time": 12.5
  }
}
```

### Deadlock Response (Partial)
```json
{
  "success": true,
  "answer": {
    "partial_solution": "Best available information",
    "areas_of_uncertainty": "Unresolved aspects",
    "what_we_can_conclude": "Confident conclusions",
    "recommendations_for_further_exploration": "Suggested research directions"
  }
}
```

## Quality Indicators

- **Verification Level**: high | medium | limited
- **Context Support**: strong | moderate | limited  
- **Debate Status**: converged | deadlock
- **Convergence Score**: 0.0-1.0 (confidence in final answer)

## Performance Metrics

The system tracks comprehensive performance metrics:

- **Convergence Rate**: Percentage of queries that reach satisfactory conclusions
- **Average Debate Rounds**: Mean number of iterations per query
- **Deadlock Rate**: Percentage of queries that reach maximum rounds without convergence
- **Agent Performance**: Individual agent execution times and success rates

## Dependencies

Core dependencies are shared with the parent RAG system:

- FastAPI for REST API
- LangChain for LLM orchestration
- Google Gemini for language model
- Pydantic for data validation
- asyncio for concurrent processing

## Development

### Running Tests
```bash
# Run the integrated system test
python -m pytest tests/ -v

# Test individual agents
python -m pytest tests/test_agents.py -v
```

### Adding New Agents

1. Create agent class inheriting from `BaseAgent`
2. Implement the `process()` method
3. Register with `AgentRegistry` in orchestrator
4. Update orchestrator workflow logic

### Configuration Tuning

Key parameters to adjust based on use case:

- `max_debate_rounds`: Higher for complex domains, lower for speed
- `retrieval_k`: More for comprehensive coverage, fewer for efficiency  
- `convergence_threshold`: Higher for stricter quality, lower for faster responses
- `speculation_rounds`: More for difficult queries, fewer for efficiency

## Integration Points

The system integrates with:

1. **RAG System** (port 8002) - For document retrieval
2. **Backend Chat** (port 8000) - Via model="speculative"
3. **LLM Services** - Gemini, OpenAI, Anthropic (configurable)

## Monitoring

Monitor system health via:

```bash
# System status
curl http://localhost:8003/status

# Agent health  
curl http://localhost:8003/health/agents

# Configuration (debug mode only)
curl http://localhost:8003/debug/config
```

## Troubleshooting

Common issues:

1. **Service Unavailable (503)**: RAG system or LLM client not initialized
2. **No Context Found**: Ensure course_id exists in vector database  
3. **Debate Deadlock**: Check critique severity thresholds in config
4. **High Processing Time**: Reduce max_debate_rounds or retrieval_k

## Architecture Principles

The system follows key principles from the requirements:

- **Pragmatic Pattern Usage**: Only applies complexity where it adds clear value
- **Single Responsibility**: Each agent has one clear purpose
- **Composition over Inheritance**: Agents are composed, not derived
- **Rule of Three**: Abstractions only after proven need across agents
- **Clean Separation**: Business logic separate from configuration

This ensures the system remains maintainable while providing advanced reasoning capabilities. 