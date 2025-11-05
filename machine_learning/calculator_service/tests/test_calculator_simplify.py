"""
Unit tests for CalculatorService - simplify mode
"""
import pytest
import sympy as sp
from service.calculator import CalculatorService
from model.compute_request_model import (
    ComputeRequest,
)


class TestCalculatorSimplify:
    """Test cases for simplify mode"""

    def setup_method(self):
        """Setup test fixtures"""
        self.service = CalculatorService()

    def test_simplify_basic(self):
        """Test basic simplification"""
        request = ComputeRequest(mode="simplify", expr="x + x")
        result = self.service.compute(request)
        assert result["ok"] is True
        # Result is now a SymPy Expr, not a string
        assert isinstance(result["result"], sp.Expr)
        assert "2*x" in str(result["result"]) or "2x" in str(result["result"])

    def test_simplify_expression(self):
        """Test expression simplification"""
        request = ComputeRequest(mode="simplify", expr="(x**2 - 1)/(x - 1)")
        result = self.service.compute(request)
        assert result["ok"] is True
        # Result is now a SymPy Expr, not a string
        assert isinstance(result["result"], sp.Expr)
