"""
Integration tests for FastAPI endpoints
"""
import pytest
from fastapi.testclient import TestClient
from main import app


class TestAPI:
    """Test cases for FastAPI endpoints"""

    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)

    def test_root_endpoint(self):
        """Test root endpoint"""
        response = self.client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "Calculator Service" in data["message"]

    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_compute_eval_basic(self):
        """Test compute endpoint with eval mode"""
        response = self.client.post("v1/compute", json={"mode": "eval", "expr": "2 + 2"})
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["result"] == 4.0
        assert data["mode"] == "eval"

    def test_compute_eval_complex(self):
        """Test compute endpoint with complex expression"""
        response = self.client.post(
            "/v1/compute", json={"mode": "eval", "expr": "sqrt(16) + sin(pi/2)"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert isinstance(data["result"], (int, float))

    def test_compute_simplify(self):
        """Test compute endpoint with simplify mode"""
        response = self.client.post(
            "v1/compute", json={"mode": "simplify", "expr": "x + x"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert isinstance(data["result"], str)

    def test_compute_differentiate(self):
        """Test compute endpoint with differentiate mode"""
        response = self.client.post(
            "v1/compute", json={"mode": "differentiate", "expr": "x**2", "var": "x"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert isinstance(data["result"], (str, float))

    def test_compute_integrate_indefinite(self):
        """Test compute endpoint with indefinite integral"""
        response = self.client.post(
            "v1/compute", json={"mode": "integrate", "expr": "x**2", "var": "x"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert isinstance(data["result"], (str, float))

    def test_compute_integrate_definite(self):
        """Test compute endpoint with definite integral"""
        response = self.client.post(
            "v1/compute",
            json={
                "mode": "integrate",
                "expr": "x**2",
                "var": "x",
                "lower": "0",
                "upper": "2",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert isinstance(data["result"], (str, float))

    def test_compute_solve(self):
        """Test compute endpoint with solve mode"""
        response = self.client.post(
            "v1/compute", json={"mode": "solve", "expr": "x**2 - 4", "var": "x"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert isinstance(data["result"], (list, tuple))

    def test_compute_invalid_expression(self):
        """Test compute endpoint with invalid expression"""
        response = self.client.post(
            "v1/compute", json={"mode": "eval", "expr": "invalid@#$%expression"}
        )
        # Should return error (either 422 or 200 with ok=False)
        assert response.status_code in [200, 422]

    def test_compute_missing_var(self):
        """Test compute endpoint with missing var parameter"""
        response = self.client.post(
            "v1/compute",
            json={
                "mode": "differentiate",
                "expr": "x**2"
                # Missing var parameter
            },
        )
        # Should return validation error
        assert response.status_code == 422

    def test_compute_expression_too_long(self):
        """Test compute endpoint with expression too long"""
        long_expr = "x" * 501
        response = self.client.post(
            "v1/compute", json={"mode": "eval", "expr": long_expr}
        )
        assert response.status_code == 422

    def test_compute_illegal_expression(self):
        """Test compute endpoint with illegal expression"""
        response = self.client.post(
            "v1/compute", json={"mode": "eval", "expr": "__class__"}
        )
        assert response.status_code == 422

    def test_compute_invalid_mode(self):
        """Test compute endpoint with invalid mode"""
        response = self.client.post(
            "v1/compute", json={"mode": "invalid_mode", "expr": "2 + 2"}
        )
        # Should return validation error
        assert response.status_code == 422
