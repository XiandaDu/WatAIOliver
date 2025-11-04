import datetime
import logging
import sympy as sp
from typing import Callable, Optional, List, Union
from sympy.parsing.sympy_parser import parse_expr
from exceptions import ComputationError, MissingParameterError, ParseError
from model.compute_request_model import ComputeRequest

logger = logging.getLogger("calculator_service.calculator")

# Security whitelist: Only allow safe SymPy functions and types
# This prevents users from calling dangerous functions
SAFE_FUNCTIONS = {
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "asin": sp.asin,
    "acos": sp.acos,
    "atan": sp.atan,
    "log": sp.log,
    "ln": sp.log,  # ln is an alias for the natural logarithm
    "exp": sp.exp,
    "sqrt": sp.sqrt,
    "pi": sp.pi,
    "E": sp.E,
    "I": sp.I,
    "oo": sp.oo,
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
            result = parse_expr(expr, local_dict=SAFE_FUNCTIONS, global_dict={})
            logger.debug("Expression parsed successfully")
            return result
        except Exception as e:
            logger.error(f"Expression parsing failed: {str(e)}")
            raise ValueError(f"Expression parsing failed: {str(e)}")

    def _eval(self, expr: sp.Expr) -> float:
        try:
            return sp.N(expr)
        except Exception as e:
            raise ComputationError(f"Error evaluating expression: {e}")

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
            raise ComputationError(f"Error simplifying expression: {e}")

    def _differentiate(self, expr: sp.Expr, var: sp.Symbol) -> sp.Expr:
        try:
            return sp.diff(expr, var)
        except Exception as e:
            raise ComputationError(f"Error differentiating expression: {e}")

    def _integrate(
        self,
        expr: sp.Expr,
        var: sp.Symbol,
        lower: Optional[sp.Expr] = None,
        upper: Optional[sp.Expr] = None,
    ) -> sp.Expr:
        try:
            # For definite integral: sp.integrate(expr, (var, lower, upper))
            # For indefinite integral: sp.integrate(expr, var)
            if lower is not None and upper is not None:
                return sp.integrate(expr, (var, lower, upper))
            else:
                return sp.integrate(expr, var)

        except Exception as e:
            raise ComputationError(f"Error integrating expression: {e}")

    def _solve(self, expr: sp.Expr, var: sp.Symbol) -> List:
        try:
            return sp.solve(expr, var)
        except Exception as e:
            raise ComputationError(f"Error solving expression: {e}")

    def compute(self, request: ComputeRequest) -> dict:
        # assume request is valid (checked in main.py)
        # parse request, convert to sympy objects
        try:
            mode = request.mode
            expr = self._safe_parse_expr(request.expr)
            var = sp.Symbol(request.var) if request.var is not None else None
            lower = (
                self._safe_parse_expr(request.lower)
                if request.lower is not None
                else None
            )
            upper = (
                self._safe_parse_expr(request.upper)
                if request.upper is not None
                else None
            )
        except Exception as e:
            raise ParseError("Invalid syntax")

        # compute - return raw SymPy objects, let main.py handle serialization
        if mode == "eval":
            result = self._eval(expr)

        elif mode == "simplify":
            result = self._simplify(expr)

        elif mode == "differentiate":
            if var is None:
                raise MissingParameterError("'var' required for differentiation")
            result = self._differentiate(expr, var)

        elif mode == "integrate":
            if var is None:
                raise MissingParameterError("'var' required for integration")
            result = self._integrate(expr, var, lower, upper)

        elif mode == "solve":
            if var is None:
                raise MissingParameterError("'var' required for solving")
            result = self._solve(expr, var)

        else:
            raise ValueError(f"Invalid mode: {mode}")

        # return response with raw SymPy objects
        return {
            "ok": True,
            "result": result,  # type: Union[float, sp.Expr, List]
            "mode": mode,
        }
