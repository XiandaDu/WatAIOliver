"""
Unit tests for CalculatorService - differentiate mode
"""
import pytest
from machine_learning.calculator_service.service.calculator import CalculatorService
from machine_learning.calculator_service.model.compute_request_model import ComputeRequest


class TestCalculatorDifferentiate:
    """Test cases for differentiate mode"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.service = CalculatorService()
    
    def test_differentiate_basic(self):
        """Test basic differentiation"""
        request = ComputeRequest(mode="differentiate", expr="x**2", var="x")
        result = self.service.compute(request)
        assert result.ok is True
        assert isinstance(result.result, (str, float))
        assert "2*x" in str(result.result) or "2x" in str(result.result)
    
    def test_differentiate_polynomial(self):
        """Test polynomial differentiation"""
        request = ComputeRequest(mode="differentiate", expr="x**3 + 2*x**2", var="x")
        result = self.service.compute(request)
        assert result.ok is True
        assert isinstance(result.result, (str, float))
    
    def test_differentiate_trigonometric(self):
        """Test trigonometric differentiation"""
        request = ComputeRequest(mode="differentiate", expr="sin(x)", var="x")
        result = self.service.compute(request)
        assert result.ok is True
        assert isinstance(result.result, (str, float))

