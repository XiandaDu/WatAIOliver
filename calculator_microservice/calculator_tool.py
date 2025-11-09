"""
HTTP Calculator Tool Interface - Module 2

A LangChain StructuredTool that bridges the ReAct Agent and the calculator microservice.
Converts tool calls to HTTP requests, handles network errors and timeouts,
validates parameters and formats responses.
"""

import logging
import requests
from typing import Optional
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CalculatorInput(BaseModel):
    """Input schema for the calculator tool"""
    mode: str = Field(
        description="The computation mode: 'eval' (numerical result), 'simplify' (simplify expression), "
                   "'differentiate' (derivative), 'integrate' (integral), or 'solve' (solve equation)"
    )
    expr: str = Field(description="The mathematical expression to compute (in Python/SymPy syntax, e.g., x**2 not x^2)")
    var: Optional[str] = Field(
        default=None,
        description="The variable name for differentiation, integration, or solving (required for those modes)"
    )


def build_http_calculator_tool(service_url: str, timeout: float = 5.0) -> StructuredTool:
    """
    Build a LangChain StructuredTool for the calculator microservice.
    
    Args:
        service_url: Base URL of the calculator microservice (e.g., "http://localhost:8000")
        timeout: Request timeout in seconds (default: 5.0)
    
    Returns:
        A StructuredTool instance that can be used with LangChain agents
    """
    # Ensure service_url doesn't end with a slash
    service_url = service_url.rstrip('/')
    compute_endpoint = f"{service_url}/v1/compute"
    
    def calculator_function(mode: str, expr: str, var: Optional[str] = None) -> str:
        """
        Call the calculator microservice to perform a mathematical computation.
        
        Args:
            mode: Computation mode ('eval', 'simplify', 'differentiate', 'integrate', 'solve')
            expr: Mathematical expression in Python/SymPy syntax
            var: Variable name (required for differentiate, integrate, solve)
        
        Returns:
            String result of the computation, or error message if computation failed
        """
        # Validate mode
        valid_modes = ['eval', 'simplify', 'differentiate', 'integrate', 'solve']
        if mode not in valid_modes:
            error_msg = f"Invalid mode '{mode}'. Must be one of: {', '.join(valid_modes)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        
        # Validate that var is provided for modes that require it
        if mode in ['differentiate', 'integrate', 'solve'] and not var:
            error_msg = f"Mode '{mode}' requires a 'var' parameter specifying the variable name"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        
        # Build request payload
        payload = {
            "mode": mode,
            "expr": expr
        }
        if var:
            payload["var"] = var
        
        try:
            logger.info(f"Calling calculator service: {mode} on expression '{expr}'" + (f" with var '{var}'" if var else ""))
            
            # Make HTTP POST request
            response = requests.post(
                compute_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=timeout
            )
            
            # Check HTTP status
            if response.status_code != 200:
                error_msg = f"HTTP error {response.status_code}: {response.text}"
                logger.error(error_msg)
                return f"Error: {error_msg}"
            
            # Parse response
            result_data = response.json()
            
            # Check for computation errors
            if result_data.get("error_code"):
                error_code = result_data.get("error_code")
                error_message = result_data.get("message", "Unknown error")
                
                # Format error for ReAct agent
                formatted_error = f"Error: {error_code} - {error_message}"
                logger.warning(f"Calculator service returned error: {formatted_error}")
                return formatted_error
            
            # Return successful result
            result = result_data.get("result")
            if result is None:
                error_msg = "No result returned from calculator service"
                logger.error(error_msg)
                return f"Error: {error_msg}"
            
            logger.info(f"Calculator service returned result: {result}")
            return str(result)
            
        except requests.exceptions.Timeout:
            error_msg = f"Request to calculator service timed out after {timeout} seconds"
            logger.error(error_msg)
            return f"Error: timeout - {error_msg}"
            
        except requests.exceptions.ConnectionError:
            error_msg = f"Could not connect to calculator service at {compute_endpoint}. Is the service running?"
            logger.error(error_msg)
            return f"Error: connection failed - {error_msg}"
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request to calculator service failed: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
            
        except Exception as e:
            error_msg = f"Unexpected error calling calculator service: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return f"Error: {error_msg}"
    
    # Create and return the StructuredTool
    return StructuredTool.from_function(
        func=calculator_function,
        name="calculator",
        description=(
            "A secure mathematical calculator that performs computations using SymPy. "
            "Use this tool for ALL mathematical calculations - never calculate yourself.\n\n"
            "Modes:\n"
            "- 'eval': Evaluate expression to a numerical value (e.g., '2 + 3')\n"
            "- 'simplify': Simplify an expression (e.g., 'x**2 + 2*x + 1')\n"
            "- 'differentiate': Compute derivative (requires 'var' parameter, e.g., mode='differentiate', expr='x**2', var='x')\n"
            "- 'integrate': Compute integral (requires 'var' parameter, e.g., mode='integrate', expr='x', var='x')\n"
            "- 'solve': Solve an equation (requires 'var' parameter, e.g., mode='solve', expr='x**2 - 4', var='x')\n\n"
            "Expression format:\n"
            "- Use Python/SymPy syntax: x**2 for x² (NOT x^2)\n"
            "- Use explicit multiplication: 2*x (NOT 2x)\n"
            "- All parameters must be strings\n"
        ),
        args_schema=CalculatorInput
    )

