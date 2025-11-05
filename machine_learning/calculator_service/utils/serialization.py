"""
Serialization utilities for converting SymPy objects to JSON-serializable types
"""
import sympy as sp
from typing import Any, Union, List


def serialize_result(result: Any, mode: str) -> Union[float, str, List]:
    """
    Convert SymPy objects to JSON-serializable types.

    Args:
        result: The computation result from CalculatorService (SymPy objects)
        mode: The computation mode (eval, simplify, differentiate, integrate, solve)

    Returns:
        JSON-serializable result (float, str, or List)
    """
    if mode == "eval":
        # Convert SymPy Float/Integer/Rational to Python float
        return float(result)

    elif mode in ["simplify", "differentiate", "integrate"]:
        # Convert sp.Expr to string
        return str(result)

    elif mode == "solve":
        # Convert list of SymPy objects to list of Python types
        if not isinstance(result, list):
            return str(result)

        serialized = []
        for item in result:
            if isinstance(item, (sp.Float, sp.Integer, sp.Rational)):
                serialized.append(float(item))
            elif isinstance(item, (int, float)):
                serialized.append(item)
            else:
                # For complex expressions, convert to string
                serialized.append(str(item))
        return serialized

    return result
