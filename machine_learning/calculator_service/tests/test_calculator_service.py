"""
Unit tests for CalculatorService
"""
import pytest
from machine_learning.calculator_service.service.calculator import CalculatorService
from machine_learning.calculator_service.model.compute_request_model import ComputeRequest


class TestCalculatorService:
    """Test cases for CalculatorService"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.service = CalculatorService()
    
    # Test eval mode
    def test_eval_basic_addition(self):
        """Test basic addition"""
        request = ComputeRequest(mode="eval", expr="2 + 2")
        result = self.service.compute(request)
        assert result.ok is True
        assert result.result == 4.0
        assert result.mode == "eval"
    
    def test_eval_subtraction(self):
        """Test subtraction"""
        request = ComputeRequest(mode="eval", expr="10 - 5")
        result = self.service.compute(request)
        assert result.ok is True
        assert result.result == 5.0
    
    def test_eval_multiplication(self):
        """Test multiplication"""
        request = ComputeRequest(mode="eval", expr="3 * 4")
        result = self.service.compute(request)
        assert result.ok is True
        assert result.result == 12.0
    
    def test_eval_division(self):
        """Test division"""
        request = ComputeRequest(mode="eval", expr="15 / 3")
        result = self.service.compute(request)
        assert result.ok is True
        assert result.result == 5.0
    
    def test_eval_with_functions(self):
        """Test evaluation with mathematical functions"""
        request = ComputeRequest(mode="eval", expr="sqrt(16)")
        result = self.service.compute(request)
        assert result.ok is True
        assert abs(result.result - 4.0) < 0.001
    
    def test_eval_with_pi(self):
        """Test evaluation with pi"""
        request = ComputeRequest(mode="eval", expr="pi")
        result = self.service.compute(request)
        assert result.ok is True
        assert abs(result.result - 3.14159) < 0.001
    
    def test_eval_complex_expression(self):
        """Test complex expression"""
        request = ComputeRequest(mode="eval", expr="2 + 3 * 4 - 5")
        result = self.service.compute(request)
        assert result.ok is True
        assert result.result == 9.0
    
    # Test simplify mode
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
    
    # Test differentiate mode
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
    
    # Test integrate mode
    def test_integrate_indefinite(self):
        """Test indefinite integral"""
        request = ComputeRequest(mode="integrate", expr="x**2", var="x")
        result = self.service.compute(request)
        assert result.ok is True
        assert isinstance(result.result, (str, float))
    
    def test_integrate_definite(self):
        """Test definite integral"""
        request = ComputeRequest(
            mode="integrate",
            expr="x**2",
            var="x",
            lower="0",
            upper="2"
        )
        result = self.service.compute(request)
        assert result.ok is True
        assert isinstance(result.result, (str, float))
    
    # Test solve mode
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
    
    # Test error cases
    def test_invalid_mode(self):
        """Test invalid mode"""
        request = ComputeRequest(mode="eval", expr="2 + 2")
        # Manually change mode to invalid value
        request.mode = "invalid_mode"
        with pytest.raises(ValueError):
            self.service.compute(request)
    
    # Test _safe_parse_expr method directly
    def test_safe_parse_expr_basic(self):
        """Test _safe_parse_expr with basic expression"""
        result = self.service._safe_parse_expr("2 + 2")
        assert result is not None
        # Verify it's a SymPy expression
        import sympy as sp
        assert isinstance(result, sp.Expr)
    
    def test_safe_parse_expr_with_functions(self):
        """Test _safe_parse_expr with functions"""
        result = self.service._safe_parse_expr("sqrt(16)")
        assert result is not None
        import sympy as sp
        assert isinstance(result, sp.Expr)
    
    def test_safe_parse_expr_with_variables(self):
        """Test _safe_parse_expr with variables"""
        result = self.service._safe_parse_expr("x**2 + y")
        assert result is not None
        import sympy as sp
        assert isinstance(result, sp.Expr)
    
    def test_safe_parse_expr_with_constants(self):
        """Test _safe_parse_expr with constants"""
        result = self.service._safe_parse_expr("pi + E")
        assert result is not None
        import sympy as sp
        assert isinstance(result, sp.Expr)
    
    def test_safe_parse_expr_invalid_expression(self):
        """Test _safe_parse_expr with invalid expression"""
        with pytest.raises(ValueError, match="Expression parsing failed"):
            self.service._safe_parse_expr("invalid@#$%expression")
    
    def test_safe_parse_expr_complex_expression(self):
        """Test _safe_parse_expr with complex expression"""
        result = self.service._safe_parse_expr("sin(x) * cos(y) + sqrt(x**2 + y**2)")
        assert result is not None
        import sympy as sp
        assert isinstance(result, sp.Expr)

