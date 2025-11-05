"""
Unit tests for CalculatorService - error handling
"""
import pytest
from service.calculator import CalculatorService
from model import ComputeRequest
from exceptions import (
    ParseError,
    MissingParameterError,
    ComputationError,
    ComputationTimeoutError,
)


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

    def test_parse_error_invalid_expression(self):
        """Invalid expression should raise ParseError"""
        request = ComputeRequest(mode="eval", expr="invalid@#$%expression")
        with pytest.raises(ParseError):
            self.service.compute(request)

    def test_missing_param_error(self):
        """Missing var for differentiate should raise MissingParameterError"""
        request = ComputeRequest(mode="differentiate", expr="x**2")
        with pytest.raises(MissingParameterError):
            self.service.compute(request)

    def test_compute_error_runtime(self, monkeypatch):
        """Simulate runtime failure in _eval -> ComputationError"""

        def boom(*args, **kwargs):
            raise Exception("simulated failure")

        monkeypatch.setattr(self.service, "_eval", boom)
        request = ComputeRequest(mode="eval", expr="2 + 2")
        with pytest.raises(ComputationError) as ei:
            self.service.compute(request)
        assert "COMPUTE_ERROR:" in str(ei.value)

    def test_compute_error_divide_by_zero(self, monkeypatch):
        """Division by zero should surface as ComputationError (simulated)"""

        def divzero(*args, **kwargs):
            raise ZeroDivisionError("division by zero")

        monkeypatch.setattr(self.service, "_eval", divzero)
        request = ComputeRequest(mode="eval", expr="1/0")
        with pytest.raises(ComputationError) as ei:
            self.service.compute(request)
        assert "division by zero" in str(ei.value).lower()

    @pytest.mark.xfail(
        reason="Timeout not implemented yet - pending hard timeout feature"
    )
    def test_timeout_error_pending(self):
        """Placeholder for timeout once implemented"""
        request = ComputeRequest(mode="eval", expr="2 + 2")
        with pytest.raises(ComputationTimeoutError):
            # When timeout is implemented, this should trigger a timeout
            self.service.compute(request)
