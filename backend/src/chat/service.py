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

def nebula_text_endpoint(prompt_text: str) -> str:
    """
    Sends a request to the API endpoint and returns the response.

    Args:
        document_path (str): Path to the document.
        prompt_text (str): The prompt text to be used for processing.

    Returns:
        str: The generated text from the API.
    """

    data = {
        "prompt": f"{prompt_text}",
        "reasoning": True,
    }
    
    response = requests.post(f"{BASE_URL}/generate", data)
    return response.json().get("result", "No result returned")