"""
Quick test script for _safe_parse_expr method
Run this file directly to test the method
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from service.calculator import CalculatorService
import sympy as sp


def test_safe_parse_expr():
    """Quick test for _safe_parse_expr method"""
    service = CalculatorService()
    
    test_cases = [
        ("2 + 2", "Basic addition"),
        ("sqrt(16)", "Square root function"),
        ("x**2 + y", "Variables"),
        ("sin(x) + cos(y)", "Trigonometric functions"),
        ("pi + E", "Mathematical constants"),
        ("log(10)", "Logarithm function"),
        ("exp(x)", "Exponential function"),
    ]
    
    print("=" * 60)
    print("Testing _safe_parse_expr method")
    print("=" * 60)
    
    for expr, description in test_cases:
        try:
            result = service._safe_parse_expr(expr)
            print(f"✓ {description:30} | Expression: {expr:20} | Result: {result}")
            assert isinstance(result, sp.Expr), f"Result should be SymPy expression, got {type(result)}"
        except Exception as e:
            print(f"✗ {description:30} | Expression: {expr:20} | Error: {str(e)}")
    
    # Test invalid expression
    print("\n" + "=" * 60)
    print("Testing invalid expressions")
    print("=" * 60)
    
    invalid_cases = [
        ("invalid@#$%", "Invalid characters"),
        ("", "Empty string"),
    ]
    
    for expr, description in invalid_cases:
        try:
            result = service._safe_parse_expr(expr)
            print(f"✗ {description:30} | Expression: {expr:20} | Unexpectedly succeeded: {result}")
        except ValueError as e:
            print(f"✓ {description:30} | Expression: {expr:20} | Correctly raised ValueError: {str(e)[:50]}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_safe_parse_expr()

