import requests
from backend.constants import ServiceConfig

BASE_URL = ServiceConfig.NEBULA_BASE_URL  # This is the stable endpoint

def generate(prompt: str, reasoning: bool = False) -> str:
    response = requests.post(f"{BASE_URL}/generate", data={"prompt": prompt, "reasoning": reasoning})
    response.raise_for_status()
    data = response.json()
    if "result" not in data:
        raise ValueError("LLM API response missing 'result' field")
    return data["result"]

def generate_vision(prompt: str, image_path: str, fast: bool = False) -> str:
    with open(image_path, "rb") as img:
        files = {"file": img}
        data = {"prompt": prompt, "fast": str(fast).lower()}
        response = requests.post(f"{BASE_URL}/generate_vision", data=data, files=files)
    response.raise_for_status()
    data = response.json()
    if "result" not in data:
        raise ValueError("LLM API response missing 'result' field")
    return data["result"]
