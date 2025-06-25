# ai_grading

The AI Grading project is broken into two pieces - the APIs (described in detail here) and the apps (included in the git repo but not described there).

The idea is to use the API to write your own apps that solve a piece of grading functionality. Before writing any apps, it is recommended that you install the APIs via pip so you do not have to duplicate them in each app

---

# extract_api

## Overview

This project provides a flexible framework for processing various types of files, including PDFs, DOCX files, and compressed archives (ZIP, TAR). The core components include:

- **FileProcessor**: An abstract base class for processing files.
- **ProcessingStep**: A class for defining processing steps within a project.
- **Project**: A class to manage and execute a sequence of processing steps.

## Classes

### FileProcessor (Abstract Base Class)

- **Attributes:**
  - `input_path` (str): Path to the input file or directory.
  - `output_path` (str): Path to the output directory.

- **Methods:**
  - `__init__(input_path, output_path)`: Initializes the FileProcessor with the input and output paths.
  - `ensure_output_directory()`: Ensures that the output directory exists. Creates it if necessary.
  - `process()`: Abstract method for processing files. Must be implemented by subclasses.

### ProcessingStep

- **Attributes:**
  - `processor_class`: The class responsible for processing files.
  - `mode` (str): Mode of operation ('flat', 'subdirs', 'converge').
  - `kwargs`: Additional keyword arguments for the processor class.

- **Methods:**
  - `__init__(processor_class, mode='flat', **kwargs)`: Initializes the processing step.

### Project

- **Attributes:**
  - `name` (str): Name of the project.
  - `base_input_path` (str): Path to the base input directory or file.
  - `base_output_path` (str): Path to the base output directory.
  - `steps` (List[ProcessingStep]): List of processing steps.

- **Methods:**
  - `__init__(name: str, base_input_path: str, base_output_path: str)`: Initializes the project with the given name, input, and output paths.
  - `add_step(processor_class, mode='flat', **kwargs)`: Adds a processing step to the project.
  - `run()`: Executes the processing steps in sequence.
  - `_process_file(step: ProcessingStep, input_path: str, output_path: str)`: Processes a single file.
  - `_process_directory(step: ProcessingStep, input_dir: str, output_dir: str)`: Processes a directory of files.
  - `_process_flat_directory(step: ProcessingStep, input_dir: str, output_dir: str)`: Processes files in a flat directory structure.

## Usage

1. **Define a FileProcessor Subclass:**
   Implement the `FileProcessor` class to handle specific file types and processing needs. For example, you might create a `PDFProcessor` class to process PDF files.

2. **Create a Project:**
   Instantiate the `Project` class with the desired input and output paths.

   ```python
   project = Project(name="ExampleProject", base_input_path="/path/to/input", base_output_path="/path/to/output")
   ```

3. **Add Processing Steps:**
   Add processing steps to the project using the `add_step` method. Specify the processing class, mode, and any additional arguments.

   ```python
   project.add_step(PDFProcessor, mode='flat', some_argument=value)
   ```

4. **Run the Project:**
   Execute the project to process files according to the defined steps.

   ```python
   project.run()
   ```

## Modes

- **'flat'**: Processes files in a flat directory structure.
- **'subdirs'**: Processes files in a directory structure with subdirectories.
- **'converge'**: Special mode for consolidating files from subdirectories into a single directory.

## Example

Here's a simple example of how to set up and run a project:

```python
class PDFProcessor(FileProcessor):
    def process(self):
        # Implementation for processing PDF files
        pass

project = Project(name="PDFProcessing", base_input_path="/path/to/pdfs", base_output_path="/path/to/output")
project.add_step(PDFProcessor, mode='flat')
project.run()
```

# `evaluate_api.py`

This module is designed to evaluate various types of documents (text, docx, and images) using predefined prompts by sending requests to an API endpoint. It offers a flexible framework for text and image analysis through different classes.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
  - [Endpoints](#endpoints)
  - [Classes](#classes)
    - [Evaluation](#evaluation)
    - [TextToTextEvaluator](#texttotextevaluator)
    - [DocxToTextEvaluator](#docxtotextevaluator)
    - [ImageToTextEvaluator](#imagetotextevaluator)
- [Examples](#examples)
- [License](#license)

## Installation

To use the `evaluate_api.py` module, you need to have the following libraries installed:

- `requests`
- `python-docx` (for handling `.docx` files)

You can install these dependencies using pip:

```bash
pip install requests python-docx
```

## Usage

The `evaluate_api.py` module contains several classes and functions for evaluating documents against prompts using a specified API endpoint. Below is an overview of the provided endpoints and classes.

### Endpoints

#### `nebula_api_text_text_endpoint(document_text: str, prompt_text: str, max_length: int) -> str`

This function sends a request to the Nebula API for processing text documents.

**Parameters:**

- `document_text` (str): The text content of the document to be evaluated.
- `prompt_text` (str): The prompt text used to guide the evaluation.
- `max_length` (int): The maximum length of the generated response.

**Returns:**

- `str`: The response generated by the API.

#### `nebula_api_image_text_endpoint(image_path: str, prompt_text: str, url: str = "http://ece-nebula04.eng.uwaterloo.ca:8000/analyze_image/") -> dict`

This function sends a request to the Nebula API for processing image documents.

**Parameters:**

- `image_path` (str): Path to the image file to be evaluated.
- `prompt_text` (str): The prompt text used to guide the evaluation.
- `url` (str): The URL of the API endpoint. Defaults to the Nebula image analysis endpoint.

**Returns:**

- `dict`: The JSON response from the API.

### Classes

#### `Evaluation`

A generic class for evaluating documents against prompts using a specified endpoint function.

**Attributes:**

- `documents_path` (str): Path to the directory containing the documents.
- `prompts` (list): List of prompt files to be used for evaluation.
- `endpoint` (callable): Function to be called for processing each document with each prompt.
- `max_length` (int): Maximum length of the generated text (applicable for text evaluation).

**Methods:**

- `run_evaluation()`: Runs the evaluation process, calling the endpoint for each document with each prompt.
- `process_document(document_path: str, prompt_text: str, prompt_index: int)`: Processes a single document with the provided prompt using the endpoint function.
- `handle_result(document_path: str, prompt_text: str, result, prompt_index: int)`: Handles the result returned from the endpoint.

#### `TextToTextEvaluator`

A subclass of `Evaluation` for text-to-text processing using a specified API endpoint.

**Attributes:**

- `documents_path` (str): Path to the directory containing the text documents.
- `prompts` (list): List of prompt files to be used for evaluation.
- `output_path` (str): Path to the directory where output files will be saved.
- `endpoint` (callable): Function to be called for processing each document with each prompt (default: `nebula_api_text_text_endpoint`).
- `max_length` (int): Maximum length of the generated text (default: 512).

**Methods:**

- `extract_text_from_txt(document_path: str) -> str`: Extracts text from a plain text file.
- `process_document(document_path: str, prompt_text: str, prompt_index: int)`: Processes a single text document with the provided prompt using the endpoint function.
- `handle_result(document_path: str, prompt_text: str, result: str, prompt_index: int)`: Saves the result to a new file in the output directory.

#### `DocxToTextEvaluator`

A subclass of `Evaluation` for `.docx`-to-text processing using a specified API endpoint.

**Attributes:**

- `documents_path` (str): Path to the directory containing the `.docx` documents.
- `prompts` (list): List of prompt files to be used for evaluation.
- `output_path` (str): Path to the directory where output files will be saved.
- `endpoint` (callable): Function to be called for processing each document with each prompt (default: `nebula_api_text_text_endpoint`).
- `max_length` (int): Maximum length of the generated text (default: 512).

**Methods:**

- `extract_text_from_docx(docx_path: str) -> str`: Extracts text from a `.docx` file.
- `process_document(document_path: str, prompt_text: str, prompt_index: int)`: Processes a single `.docx` document with the provided prompt using the endpoint function.
- `handle_result(document_path: str, prompt_text: str, result: str, prompt_index: int)`: Saves the result to a new file in the output directory.

#### `ImageToTextEvaluator`

A subclass of `Evaluation` for image-to-text processing using a specified API endpoint.

**Attributes:**

- `documents_path` (str): Path to the directory containing the image files.
- `prompts` (list): List of prompt files to be used for evaluation.
- `output_path` (str): Path to the directory where output files will be saved.
- `endpoint` (callable): Function to be called for processing each image with each prompt (default: `nebula_api_image_text_endpoint`).

**Methods:**

- `process_document(document_path: str, prompt_text: str, prompt_index: int)`: Processes a single image document with the provided prompt using the endpoint function.
- `handle_result(document_path: str, prompt_text: str, result: dict, prompt_index: int)`: Saves the result to a new file in the output directory.

## Examples

Here is a basic example of how to use the `TextToTextEvaluator` class:

```python
from evaluate_api import TextToTextEvaluator

documents_path = "./text_documents/"
prompts = ["./prompts/prompt1.txt", "./prompts/prompt2.txt"]
output_path = "./output/"

evaluator = TextToTextEvaluator(
    documents_path=documents_path,
    prompts=prompts,
    output_path=output_path,
    max_length=512
)

evaluator.run_evaluation()
```
