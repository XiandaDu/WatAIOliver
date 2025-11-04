"""
Unit tests for CalculatorService - solve mode
"""
import pytest
from machine_learning.calculator_service.service.calculator import CalculatorService
from machine_learning.calculator_service.model.compute_request_model import ComputeRequest


class TestCalculatorSolve:
    """Test cases for solve mode"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.service = CalculatorService()
    
    def test_solve_linear_equation(self):
        """Test solving linear equation"""
        request = ComputeRequest(mode="solve", expr="2*x + 4", var="x")
        result = self.service.compute(request)
        assert result.ok is True
        assert isinstance(result.result, (list, tuple))
    
    def test_solve_quadratic_equation(self):
        """Test solving quadratic equation"""
        request = ComputeRequest(mode="solve", expr="x**2 - 4", var="x")
        result = self.service.compute(request)
        assert result.ok is True
        assert isinstance(result.result, (list, tuple))
        # Should have 2 solutions: -2 and 2
        assert len(result.result) == 2

