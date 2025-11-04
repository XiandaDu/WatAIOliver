"""
Unit tests for expression validator
"""
import pytest
from machine_learning.calculator_service.service.validator import validate_expression


class TestValidator:
    """Test cases for expression validator"""
    
    def test_valid_expression(self):
        """Test valid expression"""
        is_valid, error = validate_expression("2 + 2")
        assert is_valid is True
        assert error == ""
    
    def test_valid_expression_with_functions(self):
        """Test valid expression with functions"""
        is_valid, error = validate_expression("sqrt(16) + sin(pi/2)")
        assert is_valid is True
        assert error == ""
    
    def test_valid_expression_with_variables(self):
        """Test valid expression with variables"""
        is_valid, error = validate_expression("x**2 + y**2")
        assert is_valid is True
    
    def test_expression_too_long(self):
        """Test expression exceeding length limit"""
        long_expr = "x" * 501  # 501 characters
        is_valid, error = validate_expression(long_expr)
        assert is_valid is False
        assert "too long" in error.lower()
    
    def test_expression_at_boundary(self):
        """Test expression at boundary (500 characters)"""
        valid_expr = "x" * 500  # Exactly 500 characters
        is_valid, error = validate_expression(valid_expr)
        assert is_valid is True
    
    def test_expression_with_illegal_characters(self):
        """Test expression with illegal characters"""
        is_valid, error = validate_expression("2 + 2; rm -rf /")
        assert is_valid is False
        assert "illegal characters" in error.lower()
    
    def test_expression_with_system_attributes(self):
        """Test expression with system attributes"""
        is_valid, error = validate_expression("__class__")
        assert is_valid is False
        assert "illegal system attribute" in error.lower()
    
    def test_expression_with_import(self):
        """Test expression with import statement"""
        is_valid, error = validate_expression("import os")
        assert is_valid is False
        assert "illegal system attribute" in error.lower()
    
    def test_expression_with_whitespace(self):
        """Test expression with whitespace"""
        is_valid, error = validate_expression("2 + 2 * 3")
        assert is_valid is True
    
    def test_expression_with_parentheses(self):
        """Test expression with parentheses"""
        is_valid, error = validate_expression("(2 + 2) * 3")
        assert is_valid is True
    
    def test_expression_with_complex_math(self):
        """Test expression with complex mathematical operations"""
        is_valid, error = validate_expression("sin(x) + cos(y) * tan(z)")
        assert is_valid is True

