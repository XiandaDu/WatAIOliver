
def nebula_api_text_text_endpoint(document_text: str, prompt_text: str, max_length: int) -> str:
    """
    Sends a request to the API endpoint and returns the response.

    Args:
        document_path (str): Path to the document.
        prompt_text (str): The prompt text to be used for processing.
        max_length (int): Maximum length of the generated text.

    Returns:
        str: The generated text from the API.
    """
    #with open(document_path, 'r') as doc_file:
    #    document_text = doc_file.read()
    
    url = "http://ece-nebula09.eng.uwaterloo.ca:8000/generate"
    headers = {"Content-Type": "application/json"}
    data = {
        "prompt": f"{prompt_text}\n{document_text}",
        # "max_length": max_length
        "reasoning": True,
    }
    
    response = requests.post(f"{BASE_URL}/generate", data)
    return response.json().get("result", "No result returned")

    # response = requests.post(url, headers=headers, data=json.dumps(data))
    # response.raise_for_status()  # Raise an exception for HTTP errors
    # return response.json()['response']

    
def nebula_api_image_text_endpoint(image_path: str, prompt_text: str, url: str = "http://ece-nebula04.eng.uwaterloo.ca:8000/analyze_image/") -> dict:
    """
    Sends a request to the API endpoint with an image and a prompt, and returns the response.

    Args:
        image_path (str): Path to the image file.
        prompt_text (str): The prompt text to be used for processing.
        url (str): The URL of the API endpoint.

    Returns:
        dict: The JSON response from the API.
    """
    # with open(image_path, "rb") as image_file:
    #     response = requests.post(
    #         url,
    #         files={"file": image_file},
    #         data={"prompt": prompt_text}
    #     )
    fast = False

    with open(image_path, "rb") as img:
        files = {"file": img}
        data = {"prompt": prompt_text, "fast": str(fast).lower()}
        response = requests.post(f"{BASE_URL}/generate_vision", data=data, files=files)
    return response.json().get("result", "No result returned")

    # response.raise_for_status()  # Raise an exception for HTTP errors
    # return response.json()

# Function to encode the image for openAI
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')
  
  #Aggregates
def text_text_eval(document_text:str,prompt_text: str,model: str = "nemo",max_length:int = 512,api_key = None) -> str:
    """
    Aggregates text generation from various API endpoints based on the specified model.

    Args:
        document_text (str): The input document text to be processed.
        prompt_text (str): The prompt text to guide the text generation.
        model (str, optional): The model to use for text generation ("gpt-4o-mini", "gpt-4o", "phi", or "nemo"). Defaults to "nemo".
        max_length (int, optional): The maximum length of the generated text. Defaults to 512.
        api_key (str, optional): The API key for models requiring authentication. Defaults to None.

    Returns:
        str: The generated text from the selected API.
    """
    if model == "gpt-4o-mini" or model == "gpt-4o":
        return openAI_text_text_endpoint(document_text,prompt_text,max_length=max_length,model=model,api_key = api_key)
    elif model == "phi":
        return phi_moe_api_text_text_endpoint(document_text,prompt_text,max_length)
    elif model == "qwen":
        return qwen_api_text_text_endpoint(document_text,prompt_text,max_length)
    else:
        return nebula_api_text_text_endpoint(document_text,prompt_text,max_length)
