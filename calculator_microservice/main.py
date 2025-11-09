from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from enum import Enum
import sympy as sp
from typing import Optional
import concurrent.futures
from concurrent.futures import TimeoutError as FutureTimeoutError

class ComputeMode(str, Enum):
    eval = "eval"
    simplify = "simplify"
    differentiate = "differentiate"
    integrate = "integrate"
    solve = "solve"

class ComputeRequest(BaseModel):
    mode: ComputeMode
    expr: str
    var: Optional[str] = None

class ComputeResponse(BaseModel):
    result: Optional[str] = None
    error_code: Optional[str] = None
    message: str

class ExpressionTooLongError(Exception):
    pass

class MissingParameterError(Exception):
    pass

def secure_parse(expr: str) -> sp.Expr | str:
    """
    Parse a mathematical expression string into a SymPy expression with security checks.
    """
    # Check expression length for security (prevents DoS attacks)
    if len(expr) > 500:
        raise ExpressionTooLongError("expression exceeds maximum length of 500 characters")

    # Whitelist of safe mathematical functions and constants
    local_dict = {
        # Mathematical constants
        'pi': sp.pi,
        'E': sp.E,
        'e': sp.E,
        'S': sp.S,

        # Trigonometric functions
        'sin': sp.sin,
        'cos': sp.cos,
        'tan': sp.tan,
        'asin': sp.asin,
        'acos': sp.acos,
        'atan': sp.atan,
        'sinh': sp.sinh,
        'cosh': sp.cosh,
        'tanh': sp.tanh,

        # Exponential and logarithmic functions
        'exp': sp.exp,
        'log': sp.log,
        'ln': sp.ln,

        # Power and root functions
        'sqrt': sp.sqrt,
        'Pow': sp.Pow,

        # Absolute value and sign functions
        'Abs': sp.Abs,
        'sign': sp.sign,

        # Special functions
        'factorial': sp.factorial,
        'gamma': sp.gamma,
    }

    try:
        # Parse the expression using our restricted function whitelist
        parsed_expr = sp.parse_expr(expr, local_dict=local_dict)

        # Additional validation to catch malformed expressions
        try:
            parsed_str = str(parsed_expr)
            original_clean = expr.replace(' ', '')  # Remove spaces for comparison

            # Check for invalid operator sequences that indicate malformed input
            invalid_patterns = ['+++', '**+', '+*', '++', '--', '/*', '*/']
            if any(pattern in original_clean for pattern in invalid_patterns):
                return f"parse_error: expression contains invalid operator sequences"

            # Validate that symbol names don't contain suspicious characters
            symbols = parsed_expr.free_symbols
            for symbol in symbols:
                symbol_name = str(symbol)
                # Flag symbols with operators or excessively long names
                if len(symbol_name) > 20 or any(c in symbol_name for c in ['+', '-', '*', '/', '^', '(', ')']):
                    return f"parse_error: expression parsing resulted in invalid symbols"

        except Exception:
            pass  # Continue if additional validation fails

        return parsed_expr
    except Exception as e:
        return f"parse_error: {str(e)}"

def execute_computation(mode: ComputeMode, expr: sp.Expr, var: Optional[str]) -> str:
    """
    Execute the requested mathematical computation on the parsed expression.
    """
    if mode == ComputeMode.eval:
        # Evaluate expression to numerical value
        result = sp.N(expr)
    elif mode == ComputeMode.simplify:
        # Attempt to simplify the expression, preferring factored polynomials when appropriate
        simplified = sp.simplify(expr)
        try:
            factored = sp.factor(expr)
            if factored != simplified and len(str(factored)) <= len(str(simplified)) * 1.5:
                result = factored
            else:
                result = simplified
        except:
            # Fall back to simplified version if factoring fails
            result = simplified
    elif mode == ComputeMode.differentiate:
        # Compute derivative with respect to specified variable
        if var is None:
            raise MissingParameterError("variable required for differentiation")
        result = sp.diff(expr, sp.Symbol(var))
    elif mode == ComputeMode.integrate:
        if var is None:
            raise MissingParameterError("variable required for integration")
        result = sp.integrate(expr, sp.Symbol(var))
    elif mode == ComputeMode.solve:
        if var is None:
            raise MissingParameterError("variable required for solving")
        result = sp.solve(expr, sp.Symbol(var))
    else:
        raise ValueError(f"unsupported computation mode: {mode}")

    return str(result)

app = FastAPI(title="Calculator Microservice", version="1.0.0")

@app.get("/health")
async def health_check():
    """Health check endpoint to verify service availability"""
    return {"status": "ok"}

@app.post("/v1/compute", response_model=ComputeResponse)
async def compute(request: ComputeRequest):
    """
    Main computation endpoint that processes mathematical expressions.
    """
    try:
        # Parse and validate the input expression for security
        parsed_result = secure_parse(request.expr)

        if isinstance(parsed_result, str) and parsed_result.startswith("parse_error"):
            # Return parsing error if expression is invalid
            return ComputeResponse(
                result=None,
                error_code="parse_error",
                message=parsed_result
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(execute_computation, request.mode, parsed_result, request.var)

            try:
                # Wait for result with 3-second timeout for security
                result_str = future.result(timeout=3.0)

                return ComputeResponse(
                    result=result_str,
                    error_code=None,
                    message="computation completed successfully"
                )

            except FutureTimeoutError:
                # Cancel computation if it exceeds timeout
                future.cancel()
                return ComputeResponse(
                    result=None,
                    error_code="timeout",
                    message="computation timed out after 3 seconds"
                )

    except ExpressionTooLongError as e:
        return ComputeResponse(
            result=None,
            error_code="length_error",
            message=str(e)
        )
    except MissingParameterError as e:
        return ComputeResponse(
            result=None,
            error_code="missing_param",
            message=str(e)
        )
    except Exception as e:
        # Handle any unexpected computation errors
        return ComputeResponse(
            result=None,
            error_code="compute_error",
            message=f"computation failed: {str(e)}"
        )
