"""
Unit tests for CalculatorService - simplify mode
"""
import pytest
from machine_learning.calculator_service.service.calculator import CalculatorService
from machine_learning.calculator_service.model.compute_request_model import ComputeRequest


class TestCalculatorSimplify:
    """Test cases for simplify mode"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.service = CalculatorService()
    
    def test_simplify_basic(self):
        """Test basic simplification"""
        request = ComputeRequest(mode="simplify", expr="x + x")
        result = self.service.compute(request)
        assert result.ok is True
        assert isinstance(result.result, str)
        assert "2*x" in str(result.result) or "2x" in str(result.result)
    
    def test_simplify_expression(self):
        """Test expression simplification"""
        request = ComputeRequest(mode="simplify", expr="(x**2 - 1)/(x - 1)")
        result = self.service.compute(request)
        assert result.ok is True
        assert isinstance(result.result, str)

