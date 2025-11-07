#!/usr/bin/env python3
"""
Simple test script to demonstrate communication with the Calculator Microservice API.
"""

import requests
import json

def test_api():
    """Test the calculator API with a simplify operation."""

    # API endpoint
    url = "http://127.0.0.1:8080/v1/compute"

    # Request payload: simplify sin(x)**2 + cos(x)**2
    payload = {
        "mode": "simplify",
        "expr": "sin(x)**2 + cos(x)**2"
    }

    # Headers
    headers = {
        "Content-Type": "application/json"
    }

    try:
        # Send POST request
        response = requests.post(url, json=payload, headers=headers)

        # Print the JSON response
        print("API Response:")
        print(json.dumps(response.json(), indent=2))

        # Check if successful
        if response.status_code == 200 and response.json().get("error_code") is None:
            print("\n✓ API test successful!")
        else:
            print("\n✗ API test failed!")

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to API: {e}")
        print("\nMake sure the server is running on http://127.0.0.1:8080")

if __name__ == "__main__":
    test_api()
