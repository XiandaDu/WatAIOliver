"""
Unit tests for CalculatorService - error handling
"""
import pytest
from service.calculator import CalculatorService
from model import ComputeRequest
from exceptions import ParseError


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
        with pytest.raises(ParseError):
            self.service.compute(request)
