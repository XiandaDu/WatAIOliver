import os
import requests
import json
from docx import Document

#Endpoints
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
        "max_length": max_length
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()  # Raise an exception for HTTP errors
    print(response.json())
    return response.json()['response']

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
    with open(image_path, "rb") as image_file:
        response = requests.post(
            url,
            files={"file": image_file},
            data={"prompt": prompt_text}
        )

    response.raise_for_status()  # Raise an exception for HTTP errors
    return response.json()

#Classes

class Evaluation:
    """
    A generic class for evaluating documents against prompts using a specified endpoint function.
    
    Attributes:
        documents_path (str): Path to the directory containing the documents.
        prompts (list): List of prompt files to be used for evaluation.
        endpoint (callable): Function to be called for processing each document with each prompt.
    """
    def __init__(self, documents_path: str, prompts: list, endpoint: callable, max_length: int):
        """
        Initializes the Evaluation with the path to documents, prompts, and endpoint.
        
        Args:
            documents_path (str): Path to the directory containing the documents.
            prompts (list): List of prompt files to be used for evaluation.
            endpoint (callable): Function to be called for processing each document with each prompt.
        """
        self.documents_path = documents_path
        self.prompts = prompts
        self.endpoint = endpoint
        self.max_length = max_length

    def run_evaluation(self):
        """
        Runs the evaluation process, calling the endpoint for each document with each prompt.
        """
        for prompt_index,prompt in enumerate(self.prompts):
            with open(prompt, 'r') as prompt_file:
                prompt_text = prompt_file.read()

            for document in os.listdir(self.documents_path):
                try:
                  document_path = os.path.join(self.documents_path, document)
                  if os.path.isfile(document_path):
                      self.process_document(document_path, prompt_text,prompt_index)
                except:
                  print(f"Document {document} encountered an error. Skipping!")

    def process_document(self, document_path: str, prompt_text: str,prompt_index: int):
        """
        Processes a single document with the provided prompt using the endpoint function.
        
        Args:
            document_path (str): Path to the document.
            prompt_text (str): The prompt text to be used for processing.
        """
        result = self.endpoint(document_text, prompt_text,max_length=self.max_length)
        self.handle_result(document_path, prompt_text, result,prompt_index)

    def handle_result(self, document_path: str, prompt_text: str, result):
        """
        Handles the result returned from the endpoint.
        
        Args:
            document_path (str): Path to the document.
            prompt_text (str): The prompt text used for processing.
            result: The result returned by the endpoint.
        """
        # Placeholder for result handling logic (e.g., saving results, printing, etc.)
        print(f"Processed '{document_path}' with prompt from '{prompt_text}' - Result: {result}")


class TextToTextEvaluator(Evaluation):
    """
    A subclass of Evaluation for text-to-text processing using a specified API endpoint.
    
    Attributes:
        documents_path (str): Path to the directory containing the text documents.
        prompts (list): List of prompt files to be used for evaluation.
        endpoint (callable): Function to be called for processing each document with each prompt.
        output_path (str): Path to the directory where output files will be saved.
        max_length (int): Maximum length of the generated text.
    """
    
    def __init__(self, documents_path: str, prompts: list, output_path: str, 
                 endpoint: callable = nebula_api_text_text_endpoint, max_length: int = 512):
        """
        Initializes the TextToTextEvaluator with the required parameters.
        
        Args:
            documents_path (str): Path to the directory containing the text documents.
            prompts (list): List of prompt files to be used for evaluation.
            output_path (str): Path to the directory where output files will be saved.
            endpoint (callable): Function to be called for processing each document with each prompt (default: api_endpoint).
            max_length (int): Maximum length of the generated text (default: 512).
        """
        super().__init__(documents_path, prompts, endpoint,max_length)
        self.output_path = output_path
        self.max_length = max_length
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_path, exist_ok=True)
        
        # Set the endpoint function to the provided callable
        self.endpoint = endpoint

    def extract_text_from_txt(self,document_path):
        with open(document_path,'r',encoding='utf-8',errors='ignore') as reader:
          return reader.read()

    def process_document(self, document_path: str, prompt_text: str, prompt_index: int):
        """
        Processes a single docx document with the provided prompt using the endpoint function.
        
        Args:
            document_path (str): Path to the document.
            prompt_text (str): The prompt text to be used for processing.
            prompt_index (int): The index of the current prompt.
        """
        # Extract text from the docx file
        document_text = self.extract_text_from_txt(document_path)

        # Process the extracted text with the endpoint
        result = self.endpoint(document_text, prompt_text, max_length=self.max_length)
        self.handle_result(document_path, prompt_text, result, prompt_index)

    def handle_result(self, document_path: str, prompt_text: str, result: str, prompt_index: int):
        """
        Saves the result to a new file in the output directory.
        
        Args:
            document_path (str): Path to the original document.
            prompt_text (str): The prompt text used for processing.
            result (str): The generated text from the API.
        """
        document_name = os.path.basename(document_path)
        output_filename = f"{os.path.splitext(document_name)[0]}_prompt{prompt_index}.txt"
        output_path = os.path.join(self.output_path, output_filename)
        
        with open(output_path, 'w') as output_file:
            output_file.write(result)
        
        print(f"Saved result for '{document_path}' with prompt index {prompt_index} to '{output_path}'")
        

class DocxToTextEvaluator(Evaluation):
    """
    A subclass of Evaluation for docx-to-text processing using a specified API endpoint.
    
    Attributes:
        documents_path (str): Path to the directory containing the docx documents.
        prompts (list): List of prompt files to be used for evaluation.
        endpoint (callable): Function to be called for processing each document with each prompt.
        output_path (str): Path to the directory where output files will be saved.
        max_length (int): Maximum length of the generated text.
    """
    
    def __init__(self, documents_path: str, prompts: list, output_path: str, 
                 endpoint: callable = nebula_api_text_text_endpoint, max_length: int = 512):
        """
        Initializes the DocxToTextEvaluator with the required parameters.
        
        Args:
            documents_path (str): Path to the directory containing the docx documents.
            prompts (list): List of prompt files to be used for evaluation.
            output_path (str): Path to the directory where output files will be saved.
            endpoint (callable): Function to be called for processing each document with each prompt (default: api_endpoint).
            max_length (int): Maximum length of the generated text (default: 512).
        """
        super().__init__(documents_path, prompts, endpoint, max_length)
        self.output_path = output_path
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_path, exist_ok=True)

    def extract_text_from_docx(self, docx_path: str) -> str:
        """
        Extracts text from a docx file.
        
        Args:
            docx_path (str): Path to the docx file.
        
        Returns:
            str: Extracted text from the docx file.
        """
        doc = Document(docx_path)
        full_text = []
        for paragraph in doc.paragraphs:
            full_text.append(paragraph.text)
        return '\n'.join(full_text)

    def process_document(self, document_path: str, prompt_text: str, prompt_index: int):
        """
        Processes a single docx document with the provided prompt using the endpoint function.
        
        Args:
            document_path (str): Path to the document.
            prompt_text (str): The prompt text to be used for processing.
            prompt_index (int): The index of the current prompt.
        """
        # Extract text from the docx file
        document_text = self.extract_text_from_docx(document_path)

        # Process the extracted text with the endpoint
        result = self.endpoint(document_text, prompt_text, max_length=self.max_length)
        self.handle_result(document_path, prompt_text, result, prompt_index)

    def handle_result(self, document_path: str, prompt_text: str, result: str, prompt_index: int):
        """
        Saves the result to a new file in the output directory.
        
        Args:
            document_path (str): Path to the original document.
            prompt_text (str): The prompt text used for processing.
            result (str): The generated text from the API.
            prompt_index (int): The index of the prompt used.
        """
        document_name = os.path.basename(document_path)
        output_filename = f"{os.path.splitext(document_name)[0]}_prompt{prompt_index}.txt"
        output_path = os.path.join(self.output_path, output_filename)
        
        with open(output_path, 'w') as output_file:
            output_file.write(result)
        
        print(f"Saved result for '{document_path}' with prompt index {prompt_index} to '{output_path}'")
        
class ImageToTextEvaluator(Evaluation):
    """
    A subclass of Evaluation for image-to-text processing using a specified API endpoint.
    
    Attributes:
        documents_path (str): Path to the directory containing the image files.
        prompts (list): List of prompt files to be used for evaluation.
        endpoint (callable): Function to be called for processing each image with each prompt.
        output_path (str): Path to the directory where output files will be saved.
    """
    
    def __init__(self, documents_path: str, prompts: list, output_path: str, 
                 endpoint: callable = nebula_api_image_text_endpoint):
        """
        Initializes the ImageToTextEvaluator with the required parameters.
        
        Args:
            documents_path (str): Path to the directory containing the image files.
            prompts (list): List of prompt files to be used for evaluation.
            output_path (str): Path to the directory where output files will be saved.
            endpoint (callable): Function to be called for processing each image with each prompt (default: nebula_api_image_text_endpoint).
        """
        super().__init__(documents_path, prompts, endpoint, max_length=None)  # max_length is not used for images
        self.output_path = output_path
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_path, exist_ok=True)
        
        # Set the endpoint function to the provided callable
        self.endpoint = endpoint

    def process_document(self, document_path: str, prompt_text: str, prompt_index: int):
        """
        Processes a single image document with the provided prompt using the endpoint function.
        
        Args:
            document_path (str): Path to the document.
            prompt_text (str): The prompt text to be used for processing.
            prompt_index (int): The index of the current prompt.
        """
        # Process the image with the endpoint
        result = self.endpoint(document_path, prompt_text)
        self.handle_result(document_path, prompt_text, result, prompt_index)

    def handle_result(self, document_path: str, prompt_text: str, result: dict, prompt_index: int):
        """
        Saves the result to a new file in the output directory.
        
        Args:
            document_path (str): Path to the original document.
            prompt_text (str): The prompt text used for processing.
            result (dict): The generated text from the API.
            prompt_index (int): The index of the current prompt.
        """
        document_name = os.path.basename(document_path)
        output_filename = f"{os.path.splitext(document_name)[0]}_prompt{prompt_index}.txt"
        output_path = os.path.join(self.output_path, output_filename)
        
        with open(output_path, 'w') as output_file:
            output_file.write(result.get('response', 'No response received'))
        
        print(f"Saved result for '{document_path}' with prompt index {prompt_index} to '{output_path}'")
