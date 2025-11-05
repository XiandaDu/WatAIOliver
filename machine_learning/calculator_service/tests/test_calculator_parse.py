"""
Unit tests for CalculatorService - _safe_parse_expr method
"""
import pytest
import sympy as sp
from service.calculator import CalculatorService
from exceptions import ParseError


class TestCalculatorParse:
    """Test cases for _safe_parse_expr method"""

    def setup_method(self):
        """Setup test fixtures"""
        self.service = CalculatorService()

    def test_safe_parse_expr_basic(self):
        """Test _safe_parse_expr with basic expression"""
        result = self.service._safe_parse_expr("2 + 2")
        assert result is not None
        assert isinstance(result, sp.Expr)

    def test_safe_parse_expr_with_functions(self):
        """Test _safe_parse_expr with functions"""
        result = self.service._safe_parse_expr("sqrt(16)")
        assert result is not None
        assert isinstance(result, sp.Expr)

    def test_safe_parse_expr_with_variables(self):
        """Test _safe_parse_expr with variables"""
        result = self.service._safe_parse_expr("x**2 + y")
        assert result is not None
        assert isinstance(result, sp.Expr)

    def test_safe_parse_expr_with_constants(self):
        """Test _safe_parse_expr with constants"""
        result = self.service._safe_parse_expr("pi + E")
        assert result is not None
        assert isinstance(result, sp.Expr)

    def test_safe_parse_expr_invalid_expression(self):
        """Test _safe_parse_expr with invalid expression"""
        with pytest.raises(ParseError, match="PARSE_ERROR: Expression parsing failed"):
            self.service._safe_parse_expr("invalid@#$%expression")

    def test_safe_parse_expr_empty_string(self):
        """Empty string should raise ParseError"""
        with pytest.raises(ParseError, match="PARSE_ERROR: Expression parsing failed"):
            self.service._safe_parse_expr("")

    def test_safe_parse_expr_complex_expression(self):
        """Test _safe_parse_expr with complex expression"""
        result = self.service._safe_parse_expr("sin(x) * cos(y) + sqrt(x**2 + y**2)")
        assert result is not None
        assert isinstance(result, sp.Expr)
