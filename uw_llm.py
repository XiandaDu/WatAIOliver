import requests

BASE_URL = "http://ece-nebula07.eng.uwaterloo.ca:8976"  # This is the stable endpoint

def generate(prompt: str, reasoning: bool = False) -> str:
    response = requests.post(f"{BASE_URL}/generate", data={"prompt": prompt, "reasoning": reasoning})
    return response.json().get("result", "No result returned")

def generate_vision(prompt: str, image_path: str, fast: bool = False) -> str:
    with open(image_path, "rb") as img:
        files = {"file": img}
        data = {"prompt": prompt, "fast": str(fast).lower()}
        response = requests.post(f"{BASE_URL}/generate_vision", data=data, files=files)
    return response.json().get("result", "No result returned")
