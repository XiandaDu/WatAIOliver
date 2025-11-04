import datetime
import logging
import sympy as sp
from typing import Callable, Optional
from sympy.parsing.sympy_parser import parse_expr
from model import ComputeRequest, ComputeResponse

logger = logging.getLogger("calculator_service.calculator")

# Security whitelist: Only allow safe SymPy functions and types
# This prevents users from calling dangerous functions
SAFE_FUNCTIONS = {
    "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
    "asin": sp.asin, "acos": sp.acos, "atan": sp.atan,
    "log": sp.log, "ln": sp.log,  # ln is an alias for the natural logarithm
    "exp": sp.exp, "sqrt": sp.sqrt, "pi": sp.pi, "E": sp.E,
    "I": sp.I, "oo": sp.oo,
    
    # Basic SymPy types needed for parsing
    "Integer": sp.Integer,
    "Symbol": sp.Symbol,
    "Float": sp.Float,
    "Rational": sp.Rational,
    
    # Trigonometric functions
    # "sin": sp.sin,
    # "cos": sp.cos,
    # "tan": sp.tan,
    # "asin": sp.asin,
    # "acos": sp.acos,
    # "atan": sp.atan,
    # "atan2": sp.atan2,
    # "sinh": sp.sinh,
    # "cosh": sp.cosh,
    # "tanh": sp.tanh,
    # "asinh": sp.asinh,
    # "acosh": sp.acosh,
    # "atanh": sp.atanh,
    
    # # Logarithmic and exponential functions
    # "log": sp.log,
    # "ln": sp.log,  # ln is an alias for the natural logarithm
    # "exp": sp.exp,
    
    # # Power and root functions
    # "sqrt": sp.sqrt,
    # "cbrt": sp.cbrt,
    # "root": sp.root,
    # "Pow": sp.Pow,
    
    # # Mathematical constants
    # "pi": sp.pi,
    # "E": sp.E,
    # "I": sp.I,
    # "oo": sp.oo,
    # "zoo": sp.zoo,
    # "nan": sp.nan,
    
    # # Additional useful functions
    # "abs": sp.Abs,
    # "Abs": sp.Abs,
    # "factorial": sp.factorial,
    # "gamma": sp.gamma,
    # "erf": sp.erf,
    # "erfc": sp.erfc,
}

class CalculatorService:
    def __init__(self):
        logger.debug("CalculatorService initialized")

    def _safe_parse_expr(self, expr: str) -> sp.Expr:
        try:
            logger.debug(f"Parsing expression: {expr[:50]}...")
            # Use global_dict={} to prevent access to all SymPy functions by default
            # Only functions in SAFE_FUNCTIONS (local_dict) are allowed
            result = parse_expr(
                expr,
                local_dict=SAFE_FUNCTIONS,
                global_dict={}
            )
            logger.debug("Expression parsed successfully")
            return result
        except Exception as e:
            logger.error(f"Expression parsing failed: {str(e)}")
            raise ValueError(f"Expression parsing failed: {str(e)}")

    def _eval(self, expr: sp.Expr) -> float:
        try:
            return sp.N(expr)
        except Exception as e:
            raise ValueError(f"Error evaluating expression: {e}")

    def _simplify(
        self,
        expr: sp.Expr,
        ratio: Optional[float] = 1.7,
        measure: Optional[Callable[[sp.Expr], float]] = None,
    ) -> sp.Expr:
        try:
            kwargs = {}
            kwargs["ratio"] = ratio
            if measure is not None:
                kwargs["measure"] = measure

            logger.debug(f"Simplifying expression: {expr} with kwargs: {kwargs}")

            return sp.simplify(expr, **kwargs)

        except Exception as e:
            logger.error(f"Error simplifying expression: {e}")
            raise ValueError(f"Error simplifying expression: {e}")

    def _differentiate(self, expr: sp.Expr, var: str) -> sp.Expr:
        try:
            return sp.diff(expr, var)
        except Exception as e:
            raise ValueError(f"Error differentiating expression: {e}")

    def _integrate(
        self,
        expr: sp.Expr,
        var: str,
        lower: Optional[str] = None,
        upper: Optional[str] = None,
    ) -> sp.Expr:
        try:
            kwargs = {}
            if lower is not None:
                kwargs["lower"] = lower
            if upper is not None:
                kwargs["upper"] = upper
            return sp.integrate(expr, var, **kwargs)

        except Exception as e:
            raise ValueError(f"Error integrating expression: {e}")

    def _solve(self, expr: sp.Expr, var: str) -> sp.Expr:
        try:
            return sp.solve(expr, var)
        except Exception as e:
            raise ValueError(f"Error solving expression: {e}")

    def compute(self, request: ComputeRequest) -> ComputeResponse:
        # assume request is valid

        # parse request
        mode = request.mode
        expr = request.expr
        var = request.var
        lower = request.lower
        upper = request.upper

        # compute
        if mode == "eval":
            result = self._eval(self._safe_parse_expr(expr))
        elif mode == "simplify":
            result = self._simplify(self._safe_parse_expr(expr))
        elif mode == "differentiate":
            result = self._differentiate(self._safe_parse_expr(expr), var)
        elif mode == "integrate":
            result = self._integrate(self._safe_parse_expr(expr), var, lower, upper)
        elif mode == "solve":
            result = self._solve(self._safe_parse_expr(expr), var)
        else:
            raise ValueError(f"Invalid mode: {mode}")

        # return response
        return ComputeResponse(
            ok=True, result=result, mode=mode, timestamp=datetime.now()
        )
