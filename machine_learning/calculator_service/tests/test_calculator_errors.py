"""
Unit tests for CalculatorService - error handling
"""
import pytest
from machine_learning.calculator_service.service.calculator import CalculatorService
from machine_learning.calculator_service.model.compute_request_model import ComputeRequest


class TestCalculatorErrors:
    """Test cases for error handling"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.service = CalculatorService()
    
    def test_invalid_mode(self):
        """Test invalid mode"""
        request = ComputeRequest(mode="eval", expr="2 + 2")
        # Manually change mode to invalid value
        request.mode = "invalid_mode"
        with pytest.raises(ValueError):
            self.service.compute(request)

