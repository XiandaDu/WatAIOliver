"""
ReAct-based Strategist Agent - Module 3

Implements a ReAct engine using LangGraph's create_react_agent for mathematical problem solving.
This agent uses the calculator tool to perform all computations, never calculating itself.
"""

import logging
import os
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Load environment variables from machine_learning/.env
machine_learning_dir = Path(__file__).parent.parent / "machine_learning"
env_path = machine_learning_dir / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Fallback to default .env location
    load_dotenv()

from calculator_tool import build_http_calculator_tool

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# System prompt as specified in the design document
SYSTEM_PROMPT = """You are a professional math problem-solving strategist named "Strategist Agent." Your sole responsibility is to devise strategies for solving math problems, not to perform the actual calculations. You must strictly adhere to the following rules:

## Core Rules
1. **Absolutely No Self-Calculation**: No matter how simple the problem, you must not perform any numerical or symbolic calculations yourself. All calculations must be done by calling the 'calculator' tool. Violating this rule will result in a critical error.

2. **Strict Adherence to ReAct Format**: Each of your responses must include the following parts:
   - **Thought**: Analyze the problem, formulate a strategy, and explain why a calculation is needed and what type of calculation is required.
   - **Action**: Call the 'calculator' tool with precise parameters (mode, expr, var, etc.).
   - **Observation**: Wait for the tool to return a result, then continue thinking.
   You cannot skip or merge any steps.
   
   **IMPORTANT - When to Stop**: Once you have received a valid result from the calculator tool that answers the user's question, you MUST immediately provide your final answer WITHOUT making another tool call. The ReAct loop ends when you provide a final answer message (not a tool call). Do NOT call the calculator tool again with the same parameters. If you get the same result multiple times, you have your answer - stop and provide it to the user.
   
   **Final Answer Format**: When you have the answer, simply write your final response directly. Do NOT make another Action call. Just provide the answer in natural language.

3. **Precise Calculation Mode Specification**: Choose the correct 'mode' based on the task:
   - For a numerical result → "eval"
   - To simplify an expression → "simplify"
   - For differentiation → "differentiate" (must specify 'var')
   - For integration → "integrate" (must specify 'var'; for definite integrals from a to b, also specify 'lower'=a and 'upper'=b)
   - To solve an equation → "solve" (must specify 'var')

4. **Expression Formatting Rules**:
   - Use standard Python/SymPy syntax: x**2 for x². Absolutely do not use x^2 for powers.
   - Always use explicit multiplication: write 2*x, not 2x.
   - All parameters must be strings.
   - Avoid using LaTeX or other non-standard formats.

## Error Handling Rules
1. If the tool returns an error (Observation starts with '... Error:'), do not give up. Analyze the cause of the error in your 'Thought':
   - Syntax error in expression → Correct the expression and try again (e.g., '2x' should be '2*x').
   - Missing parameters → Add the necessary parameters (e.g., integration missing 'var').
   - Computation timeout → Try to simplify the problem or use an approximate method.

2. Try a maximum of 3 times. If it still fails, explain the problem to the user and suggest an alternative.

## Output Specification
1. The final answer must be clear and complete, including:
   - A restatement of the problem.
   - A brief description of the solution strategy.
   - The results from the tool calculations.
   - An explanation and verification of the result (if applicable).

2. Use professional yet easy-to-understand language, avoiding overly technical jargon.

3. **CRITICAL**: After receiving a valid result from the calculator tool, provide your final answer immediately. Do NOT make additional tool calls unless you need to perform a DIFFERENT calculation (e.g., if you need to evaluate the result at a specific point, or if the first calculation was incorrect).

## Important Reminders
- You have no calculation abilities; you are only a strategist.
- Every calculation must be an explicit tool call.
- Be patient and solve problems step-by-step.
- If you are unsure, ask for clarification instead of guessing.
- **STOP after getting a valid result** - do not repeat the same calculation. One tool call with a valid result is sufficient to answer the question.
"""


class ReActStrategistAgent:
    """
    ReAct-based Strategist Agent using LangGraph.
    
    This agent uses LangGraph's create_react_agent to implement the ReAct loop
    (Reasoning and Acting) for mathematical problem solving. It delegates all
    calculations to the calculator tool, never performing calculations itself.
    """
    
    def __init__(
        self,
        calculator_service_url: str,
        llm_model: str = "gemini-2.5-flash",
        temperature: float = 0.0,
        max_steps: int = 15,
        google_api_key: Optional[str] = None
    ):
        """
        Initialize the ReAct Strategist Agent.
        
        Args:
            calculator_service_url: Base URL of the calculator microservice
                (e.g., "http://localhost:8000")
            llm_model: Gemini model name to use (default: "gemini-2.5-flash")
            temperature: Temperature for LLM generation (default: 0.0 for deterministic)
            max_steps: Maximum number of ReAct steps (default: 15)
            google_api_key: Google API key (defaults to GEMINI_API_KEY env var)
        """
        self.calculator_service_url = calculator_service_url
        self.llm_model = llm_model
        self.temperature = temperature
        self.max_steps = max_steps
        self._use_system_prompt_in_call = False  # Initialize flag
        
        # Get Google API key from parameter or environment variable
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "Google API key is required. Set GEMINI_API_KEY environment variable "
                "or pass google_api_key parameter."
            )
        
        logger.info(f"Initializing ReAct Strategist Agent")
        logger.info(f"  Calculator Service: {calculator_service_url}")
        logger.info(f"  LLM Model: {llm_model}")
        logger.info(f"  Temperature: {temperature}")
        logger.info(f"  Max Steps: {max_steps}")
        
        # 1. Create the calculator tool
        self.calculator_tool = build_http_calculator_tool(
            service_url=calculator_service_url
        )
        logger.info("Calculator tool created successfully")
        
        # 2. Initialize the LLM (Gemini)
        self.llm = ChatGoogleGenerativeAI(
            model=llm_model,
            google_api_key=api_key,
            temperature=temperature
        )
        logger.info(f"LLM initialized: {llm_model}")
        
        # 3. Create the ReAct Agent with system prompt
        # The system prompt is injected via the messages prompt
        # Note: The spec shows prompt=SYSTEM_PROMPT, but create_react_agent requires
        # a ChatPromptTemplate, so we use that with fallback handling
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages")
        ])
        
        # Create the ReAct agent - try different parameter names based on LangGraph version
        try:
            # Try with state_modifier (newer versions)
            self.react_agent_graph = create_react_agent(
                model=self.llm,
                tools=[self.calculator_tool],
                state_modifier=prompt
            )
            self._use_system_prompt_in_call = False
            logger.info("ReAct agent created with state_modifier parameter")
        except TypeError:
            # Fallback to prompt parameter (older versions)
            try:
                self.react_agent_graph = create_react_agent(
                    model=self.llm,
                    tools=[self.calculator_tool],
                    prompt=prompt
                )
                self._use_system_prompt_in_call = False
                logger.info("ReAct agent created with prompt parameter")
            except TypeError:
                # Fallback: create without prompt and inject system message in __call__
                self.react_agent_graph = create_react_agent(
                    model=self.llm,
                    tools=[self.calculator_tool]
                )
                self._use_system_prompt_in_call = True
                logger.info("ReAct agent created without prompt (will inject system message in call)")
        
        logger.info("ReAct agent graph created successfully")
    
    def __call__(self, state: Dict) -> Dict:
        """
        Process a mathematical question using the ReAct agent.
        
        Args:
            state: Dictionary containing:
                - question: The mathematical question to solve (required)
                - Other state fields may be present and will be preserved
            
        Returns:
            Updated state dictionary containing:
                - All original state fields
                - intermediate_answer: The final answer (if successful)
                - status: "success" or "error"
                - error: Error message (if failed, optional)
        """
        # 1. Extract the user's question
        question = state.get("question")
        if not question:
            raise ValueError("The 'question' field is missing from the state.")
        
        logger.info("="*80)
        logger.info(f"Processing question: {question}")
        logger.info("="*80)
        
        try:
            # Build the initial messages (containing only the user question)
            if self._use_system_prompt_in_call:
                # Inject system prompt as first message if not supported in agent creation
                from langchain_core.messages import SystemMessage
                messages = [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=question)
                ]
            else:
                messages = [HumanMessage(content=question)]
            
            # Execute the ReAct loop
            logger.info("Starting ReAct loop...")
            result = self.react_agent_graph.invoke(
                {"messages": messages},
                config={"recursion_limit": self.max_steps}
            )
            
            # Extract the final answer and intermediate steps
            final_messages = result.get("messages", [])
            if not final_messages:
                raise ValueError("No messages returned from ReAct agent")
            
            final_answer = final_messages[-1].content
            
            # Extract intermediate steps (all messages except the last one, which is the final answer)
            intermediate_steps = []
            for msg in final_messages[:-1]:  # All messages except the last
                step_info = {
                    "type": msg.__class__.__name__,
                    "content": msg.content[:500] if hasattr(msg, 'content') and msg.content else str(msg)[:500]
                }
                intermediate_steps.append(step_info)
            
            logger.info("="*80)
            logger.info("ReAct loop completed successfully")
            logger.info(f"Final answer: {final_answer[:200]}...")
            logger.info(f"Intermediate steps: {len(intermediate_steps)}")
            logger.info("="*80)
            
            # Update the state
            state["intermediate_answer"] = final_answer
            state["intermediate_steps"] = intermediate_steps
            state["status"] = "success"
            
        except Exception as e:
            error_msg = (
                "Sorry, an issue occurred while processing your request. "
                "Our system engineers have been notified and are working on it."
            )
            logger.error(f"ReAct agent error: {str(e)}", exc_info=True)
            
            state["intermediate_answer"] = error_msg
            state["status"] = "error"
            state["error"] = str(e)
        
        return state
    
    def solve(self, question: str) -> Dict[str, Any]:
        """
        Convenience method for standalone usage (non-state-based interface).
        
        This method provides a simpler interface for direct question answering
        without requiring a state dictionary.
        
        Args:
            question: The mathematical question to solve
        
        Returns:
            Dictionary containing:
                - status: "success" or "error"
                - answer: The final answer (if successful)
                - error: Error message (if failed)
                - intermediate_steps: List of intermediate reasoning steps
        """
        state = {"question": question}
        result_state = self.__call__(state)
        
        # Convert state format to standalone format for backward compatibility
        return {
            "status": result_state.get("status"),
            "answer": result_state.get("intermediate_answer", ""),
            "error": result_state.get("error"),
            "intermediate_steps": result_state.get("intermediate_steps", [])
        }
    
    async def ainvoke(self, state: Dict) -> Dict:
        """
        Async version of __call__ for async workflows.
        
        Args:
            state: Dictionary containing:
                - question: The mathematical question to solve (required)
                - Other state fields may be present and will be preserved
        
        Returns:
            Updated state dictionary (same format as __call__)
        """
        # 1. Extract the user's question
        question = state.get("question")
        if not question:
            raise ValueError("The 'question' field is missing from the state.")
        
        logger.info("="*80)
        logger.info(f"Processing question (async): {question}")
        logger.info("="*80)
        
        try:
            # Build the initial messages (containing only the user question)
            if self._use_system_prompt_in_call:
                # Inject system prompt as first message if not supported in agent creation
                from langchain_core.messages import SystemMessage
                messages = [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=question)
                ]
            else:
                messages = [HumanMessage(content=question)]
            
            # Execute the ReAct loop asynchronously
            logger.info("Starting ReAct loop (async)...")
            result = await self.react_agent_graph.ainvoke(
                {"messages": messages},
                config={"recursion_limit": self.max_steps}
            )
            
            # Extract the final answer and intermediate steps
            final_messages = result.get("messages", [])
            if not final_messages:
                raise ValueError("No messages returned from ReAct agent")
            
            final_answer = final_messages[-1].content
            
            # Extract intermediate steps (all messages except the last one, which is the final answer)
            intermediate_steps = []
            for msg in final_messages[:-1]:  # All messages except the last
                step_info = {
                    "type": msg.__class__.__name__,
                    "content": msg.content[:500] if hasattr(msg, 'content') and msg.content else str(msg)[:500]
                }
                intermediate_steps.append(step_info)
            
            logger.info("="*80)
            logger.info("ReAct loop completed successfully (async)")
            logger.info(f"Final answer: {final_answer[:200]}...")
            logger.info(f"Intermediate steps: {len(intermediate_steps)}")
            logger.info("="*80)
            
            # Update the state
            state["intermediate_answer"] = final_answer
            state["intermediate_steps"] = intermediate_steps
            state["status"] = "success"
            
        except Exception as e:
            error_msg = (
                "Sorry, an issue occurred while processing your request. "
                "Our system engineers have been notified and are working on it."
            )
            logger.error(f"ReAct agent error (async): {str(e)}", exc_info=True)
            
            state["intermediate_answer"] = error_msg
            state["status"] = "error"
            state["error"] = str(e)
        
        return state
    
    async def asolve(self, question: str) -> Dict[str, Any]:
        """
        Async convenience method for standalone usage (non-state-based interface).
        
        Args:
            question: The mathematical question to solve
        
        Returns:
            Dictionary containing:
                - status: "success" or "error"
                - answer: The final answer (if successful)
                - error: Error message (if failed)
                - intermediate_steps: List of intermediate reasoning steps
        """
        state = {"question": question}
        result_state = await self.ainvoke(state)
        
        # Convert state format to standalone format for backward compatibility
        return {
            "status": result_state.get("status"),
            "answer": result_state.get("intermediate_answer", ""),
            "error": result_state.get("error"),
            "intermediate_steps": result_state.get("intermediate_steps", [])
        }

