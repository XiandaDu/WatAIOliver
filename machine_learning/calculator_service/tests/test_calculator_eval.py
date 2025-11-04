"""
Unit tests for CalculatorService - eval mode
"""
import pytest
from machine_learning.calculator_service.service.calculator import CalculatorService
from machine_learning.calculator_service.model.compute_request_model import (
    ComputeRequest,
)


class TestCalculatorEval:
    """Test cases for eval mode"""

    def setup_method(self):
        """Setup test fixtures"""
        self.service = CalculatorService()

    def test_eval_basic_addition(self):
        """Test basic addition"""
        request = ComputeRequest(mode="eval", expr="2 + 2")
        result = self.service.compute(request)
        assert result["ok"] is True
        assert result["result"] == 4.0
        assert result["mode"] == "eval"

    def test_eval_subtraction(self):
        """Test subtraction"""
        request = ComputeRequest(mode="eval", expr="10 - 5")
        result = self.service.compute(request)
        assert result["ok"] is True
        assert result["result"] == 5.0

    def test_eval_multiplication(self):
        """Test multiplication"""
        request = ComputeRequest(mode="eval", expr="3 * 4")
        result = self.service.compute(request)
        assert result["ok"] is True
        assert result["result"] == 12.0

    def test_eval_division(self):
        """Test division"""
        request = ComputeRequest(mode="eval", expr="15 / 3")
        result = self.service.compute(request)
        assert result["ok"] is True
        assert result["result"] == 5.0

    def test_eval_with_functions(self):
        """Test evaluation with mathematical functions"""
        request = ComputeRequest(mode="eval", expr="sqrt(16)")
        result = self.service.compute(request)
        assert result["ok"] is True
        assert abs(result["result"] - 4.0) < 0.001

    def test_eval_with_pi(self):
        """Test evaluation with pi"""
        request = ComputeRequest(mode="eval", expr="pi")
        result = self.service.compute(request)
        assert result["ok"] is True
        assert abs(result["result"] - 3.14159) < 0.001

    def test_eval_complex_expression(self):
        """Test complex expression"""
        request = ComputeRequest(mode="eval", expr="2 + 3 * 4 - 5")
        result = self.service.compute(request)
        assert result["ok"] is True
        assert result["result"] == 9.0
