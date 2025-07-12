import requests
import sys
import os

# Add the project root to the path so we can import config
sys.path.append(os.path.dirname(__file__))
from config.constants import ServiceConfig

BASE_URL = ServiceConfig.NEBULA_BASE_URL  # This is the stable endpoint

def generate(prompt: str, reasoning: bool = False) -> str:
    response = requests.post(f"{BASE_URL}/generate", data={"prompt": prompt, "reasoning": reasoning})
    return response.json().get("result", "No result returned")

def generate_vision(prompt: str, image_path: str, fast: bool = False) -> str:
    with open(image_path, "rb") as img:
        files = {"file": img}
        data = {"prompt": prompt, "fast": str(fast).lower()}
        response = requests.post(f"{BASE_URL}/generate_vision", data=data, files=files)
    return response.json().get("result", "No result returned")
