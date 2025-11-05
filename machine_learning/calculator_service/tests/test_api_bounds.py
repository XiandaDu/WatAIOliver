"""
API tests for bounds validation and response metadata
"""
import pytest
from fastapi.testclient import TestClient
from machine_learning.calculator_service.main import app


class TestAPIBoundsValidation:
    def setup_method(self):
        self.client = TestClient(app)

    def test_integrate_bounds_xor_validation(self):
        """Providing only lower or only upper should return 422."""
        # only lower provided
        resp1 = self.client.post(
            "/v1/compute",
            json={"mode": "integrate", "expr": "x", "var": "x", "lower": "0"},
        )
        assert resp1.status_code == 422

        # only upper provided
        resp2 = self.client.post(
            "/v1/compute",
            json={"mode": "integrate", "expr": "x", "var": "x", "upper": "1"},
        )
        assert resp2.status_code == 422

    def test_integrate_bounds_illegal_characters(self):
        """Illegal characters in bounds should be rejected with 422."""
        response = self.client.post(
            "/v1/compute",
            json={
                "mode": "integrate",
                "expr": "x",
                "var": "x",
                "lower": "0; rm -rf /",
                "upper": "1",
            },
        )
        assert response.status_code == 422

    def test_success_response_contains_timestamp(self):
        """Successful responses should include timestamp field."""
        response = self.client.post("/v1/compute", json={"mode": "eval", "expr": "2+3"})
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert data["ok"] is True
