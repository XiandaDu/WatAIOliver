"""
Example script demonstrating the ReAct-based Strategist Agent

This script shows how to use the ReAct Strategist Agent to solve mathematical problems.
Make sure the calculator microservice is running before executing this script.
"""

import asyncio
import logging
from react_strategist_agent import ReActStrategistAgent

# Configure logging to see the ReAct loop in action
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Calculator microservice URL (adjust if your service runs on a different port/URL)
CALCULATOR_SERVICE_URL = "http://localhost:8000"


def run_example():
    """Run a synchronous example"""
    print("="*80)
    print("ReAct Strategist Agent - Synchronous Example")
    print("="*80)
    
    # Initialize the agent
    agent = ReActStrategistAgent(
        calculator_service_url=CALCULATOR_SERVICE_URL,
        llm_model="gemini-2.5-flash",
        temperature=0.0,
        max_steps=15
    )
    
    # Example questions
    questions = [
        "Find the derivative of f(x) = x^3 - 3x + 2",
        "Calculate the integral of 2x",
        "Solve the equation x^2 - 4 = 0",
        "Evaluate 2 + 2 * 3",
        "Simplify (x^2 - 1) / (x - 1)"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n{'='*80}")
        print(f"Question {i}: {question}")
        print(f"{'='*80}\n")
        
        result = agent.solve(question)
        
        if result["status"] == "success":
            print(f"✅ Success!")
            print(f"Answer:\n{result['answer']}\n")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}\n")
        
        print(f"Intermediate steps: {len(result.get('intermediate_steps', []))}")


async def run_async_example():
    """Run an asynchronous example"""
    print("="*80)
    print("ReAct Strategist Agent - Asynchronous Example")
    print("="*80)
    
    # Initialize the agent
    agent = ReActStrategistAgent(
        calculator_service_url=CALCULATOR_SERVICE_URL,
        llm_model="gemini-2.5-flash",
        temperature=0.0,
        max_steps=15
    )
    
    # Example question
    question = "Find the maximum and minimum values of f(x) = x^3 - 3x + 2 on the interval [0, 2]"
    
    print(f"\n{'='*80}")
    print(f"Question: {question}")
    print(f"{'='*80}\n")
    
    result = await agent.asolve(question)
    
    if result["status"] == "success":
        print(f"✅ Success!")
        print(f"Answer:\n{result['answer']}\n")
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}\n")
    
    print(f"Intermediate steps: {len(result.get('intermediate_steps', []))}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "async":
        # Run async example
        asyncio.run(run_async_example())
    else:
        # Run sync example
        run_example()



