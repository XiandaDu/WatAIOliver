"""
Unit tests for CalculatorService - integrate mode
"""
import pytest
import sympy as sp
from machine_learning.calculator_service.service.calculator import CalculatorService
from machine_learning.calculator_service.model.compute_request_model import (
    ComputeRequest,
)


class TestCalculatorIntegrate:
    """Test cases for integrate mode"""

    def setup_method(self):
        """Setup test fixtures"""
        self.service = CalculatorService()

    def test_integrate_indefinite(self):
        """Test indefinite integral"""
        request = ComputeRequest(mode="integrate", expr="x**2", var="x")
        result = self.service.compute(request)
        assert result["ok"] is True
        assert isinstance(result["result"], sp.Expr)

    def test_integrate_definite(self):
        """Test definite integral"""
        request = ComputeRequest(
            mode="integrate", expr="x**2", var="x", lower="0", upper="2"
        )
        result = self.service.compute(request)
        assert result["ok"] is True
        assert isinstance(result["result"], sp.Expr)
