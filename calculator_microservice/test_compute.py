#!/usr/bin/env python3
"""
Simple test script to verify the calculator microservice functionality.
"""

import requests
import json
import time
import subprocess
import sys
import os

def test_health_endpoint():
    """Test the health endpoint"""
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200 and response.json() == {"status": "ok"}:
            print("✓ Health check passed")
            return True
        else:
            print("✗ Health check failed")
            return False
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return False

def test_compute_endpoint(mode, expr, var=None, expected_success=True):
    """Test the compute endpoint"""
    payload = {
        "mode": mode,
        "expr": expr
    }
    if var:
        payload["var"] = var

    try:
        response = requests.post(
            "http://localhost:8000/v1/compute",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        if expected_success:
            if response.status_code == 200:
                result = response.json()
                if result.get("error_code") is None and result.get("result"):
                    print(f"✓ {mode} computation successful: {result['result']}")
                    return True
                else:
                    print(f"✗ {mode} computation failed: {result}")
                    return False
            else:
                print(f"✗ {mode} HTTP error: {response.status_code}")
                return False
        else:
            # For error cases, we expect an error_code
            result = response.json()
            if result.get("error_code"):
                print(f"✓ {mode} correctly returned error: {result['error_code']}")
                return True
            else:
                print(f"✗ {mode} should have failed but didn't")
                return False

    except Exception as e:
        print(f"✗ {mode} error: {e}")
        return False

def test_timeout():
    """Test the timeout functionality with a complex computation"""
    # This should timeout
    payload = {
        "mode": "eval",
        "expr": "integrate(sin(x**100), (x, 0, 100))"
    }

    try:
        start_time = time.time()
        response = requests.post(
            "http://localhost:8000/v1/compute",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5  # Give extra time for our test
        )
        elapsed = time.time() - start_time

        result = response.json()
        if result.get("error_code") == "TIMEOUT":
            print(f"✓ Timeout correctly enforced after {elapsed:.2f}s")
            return True
        else:
            print(f"✗ Timeout test failed: {result}")
            return False

    except Exception as e:
        print(f"✗ Timeout test error: {e}")
        return False

def main():
    print("Testing Calculator Microservice...")

    # Test cases
    test_cases = [
        # (mode, expr, var, expected_success)
        ("eval", "2 + 3", None, True),
        ("simplify", "x**2 + 2*x + 1", None, True),
        ("differentiate", "x**2", "x", True),
        ("integrate", "x", "x", True),
        ("solve", "x**2 - 4", "x", True),

        # Error cases
        ("differentiate", "x**2", None, False),  # Missing var
        ("parse_error", "invalid syntax +++", None, False),  # Parse error
    ]

    # Start the server
    print("\nStarting server...")
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=os.path.join(os.path.dirname(__file__)),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for server to start
    time.sleep(2)

    try:
        # Test health
        if not test_health_endpoint():
            return False

        # Test compute operations
        for mode, expr, var, expected_success in test_cases:
            if not test_compute_endpoint(mode, expr, var, expected_success):
                return False

        # Test timeout
        if not test_timeout():
            return False

        print("\n✓ All tests passed!")
        return True

    finally:
        # Clean up server
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
