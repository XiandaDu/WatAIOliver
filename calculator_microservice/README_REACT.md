# ReAct Engine Implementation

This directory contains the implementation of a ReAct (Reasoning and Acting) engine based on LangGraph, as specified in the design document.

## Architecture Overview

### Module 3: ReAct Strategist Agent (`react_strategist_agent.py`)
A ReAct-based agent using LangGraph's `create_react_agent` that:
- Uses the calculator tool for all computations
- Never performs calculations itself
- Follows a strict Thought-Action-Observation loop
- Enforces the system prompt rules

## Quick Start

### Prerequisites

1. **Calculator Microservice**: Ensure the calculator microservice is running (see Module 1 implementation)
   - Default URL: `http://localhost:8000`
   - Health check: `GET http://localhost:8000/health`

2. **Dependencies**: Install required packages
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Variables**: Set your GEMINI_API_KEY key in env
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```

### Basic Usage

```python
from react_strategist_agent import ReActStrategistAgent

# Initialize the agent
agent = ReActStrategistAgent(
    calculator_service_url="http://localhost:8000",
    llm_model="gpt-4o",
    temperature=0.0,
    max_steps=15
)

# Solve a mathematical problem
result = agent("Find the derivative of f(x) = x^3 - 3x + 2")

if result["status"] == "success":
    print(f"Answer: {result['answer']}")
else:
    print(f"Error: {result['error']}")
```

### Async Usage

```python
import asyncio
from react_strategist_agent import ReActStrategistAgent

async def main():
    agent = ReActStrategistAgent(
        calculator_service_url="http://localhost:8000"
    )
    
    result = await agent.ainvoke("Calculate the integral of x^2 from 0 to 1")
    print(result["answer"])

asyncio.run(main())
```

### Running Examples

```bash
# Run the example script (synchronous)
python examples/react_agent_example.py

# Run the example script (asynchronous)
python examples/react_agent_example.py async
```

## Key Features

### 1. Strict No-Self-Calculation Policy
The agent is explicitly instructed to never perform calculations itself. All computations must go through the calculator tool.

### 2. ReAct Loop Implementation
The agent follows the standard ReAct pattern:
- **Thought**: Analyze the problem and plan the next action
- **Action**: Call the calculator tool with appropriate parameters
- **Observation**: Process the tool's result and continue reasoning

### 3. Error Recovery
The agent can recover from tool errors:
- Syntax errors → Correct the expression
- Missing parameters → Add required parameters
- Timeouts → Simplify the problem or suggest alternatives

### 4. System Prompt Enforcement
The system prompt enforces:
- Expression formatting (x**2, not x^2)
- Required parameters for each mode
- Maximum retry attempts
- Clear output format

## Tool Modes

The calculator tool supports five computation modes:

1. **eval**: Numerical evaluation
   ```python
   mode="eval", expr="2 + 2 * 3"
   ```

2. **simplify**: Expression simplification
   ```python
   mode="simplify", expr="(x^2 - 1) / (x - 1)"
   ```

3. **differentiate**: Derivative
   ```python
   mode="differentiate", expr="x^3 - 3*x + 2", var="x"
   ```

4. **integrate**: Definite or indefinite integral
   ```python
   # Indefinite
   mode="integrate", expr="x^2", var="x"
   
   # Definite
   mode="integrate", expr="x^2", var="x", lower="0", upper="1"
   ```

5. **solve**: Solve equations
   ```python
   mode="solve", expr="x^2 - 4", var="x"
   ```

## Configuration

### Agent Parameters

- `calculator_service_url` (str): Base URL of the calculator microservice
- `llm_model` (str): LLM model name (default: "gpt-4o")
- `temperature` (float): Temperature for LLM generation (default: 0.0)
- `max_steps` (int): Maximum number of ReAct steps (default: 15)

### Tool Parameters

The calculator tool accepts:
- `mode`: One of ["eval", "simplify", "differentiate", "integrate", "solve"]
- `expr`: Mathematical expression (SymPy syntax)
- `var`: Variable name (required for differentiate, integrate, solve)
- `lower`: Lower bound for definite integrals
- `upper`: Upper bound for definite integrals

## Error Handling

The implementation handles various error scenarios:

1. **Network Errors**: Connection failures, timeouts
2. **API Errors**: HTTP status errors (4xx, 5xx)
3. **Computation Errors**: Parse errors, missing parameters, timeouts
4. **Tool Errors**: Invalid tool calls, malformed responses

All errors are caught and converted to user-friendly error messages.

## Testing

To test the implementation:

1. Start the calculator microservice
2. Run the example script:
   ```bash
   python examples/react_agent_example.py
   ```

The example includes several test cases:
- Derivative calculation
- Definite integral
- Equation solving
- Numerical evaluation
- Expression simplification

## References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangGraph ReAct Agent Guide](https://langchain-ai.github.io/langgraph/how-tos/create-react-agent/)
- [LangChain Tools Documentation](https://python.langchain.com/docs/modules/tools/)

