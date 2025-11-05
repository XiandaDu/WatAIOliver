"""
Unit tests for MissingParameterError in service layer
"""
import pytest
from service.calculator import CalculatorService
from model import ComputeRequest
from exceptions import MissingParameterError


class TestCalculatorMissingParam:
    def setup_method(self):
        self.service = CalculatorService()

    def test_differentiate_missing_var_raises(self):
        req = ComputeRequest(mode="differentiate", expr="x**2")
        with pytest.raises(MissingParameterError):
            self.service.compute(req)

    def test_integrate_missing_var_raises(self):
        req = ComputeRequest(mode="integrate", expr="x")
        with pytest.raises(MissingParameterError):
            self.service.compute(req)

    def test_solve_missing_var_raises(self):
        req = ComputeRequest(mode="solve", expr="x-1")
        with pytest.raises(MissingParameterError):
            self.service.compute(req)

