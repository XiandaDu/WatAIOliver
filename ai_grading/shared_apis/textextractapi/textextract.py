import requests
import os
import zipfile
import tempfile
import shutil
from evaluate_api import *
from extract_api import *
import re

def longest_repeating_substring(s: str) -> str:
    """
    Finds and returns the longest repeating substring within the given string.

    Args:
        s (str): The input string to search for repeating substrings.

    Returns:
        str: The longest repeating substring. If no repeating substring is found, returns an empty string.
    """
    n = len(s)
    
    # Helper function to build suffix array
    def build_suffix_array(s):
        return sorted(range(n), key=lambda i: s[i:])
    
    # Helper function to build LCP array
    def build_lcp(s, suffix_array):
        rank = [0] * n
        lcp = [0] * n
        for i, suffix in enumerate(suffix_array):
            rank[suffix] = i
        
        h = 0
        for i in range(n):
            if rank[i] > 0:
                j = suffix_array[rank[i] - 1]
                while (i + h < n) and (j + h < n) and (s[i + h] == s[j + h]):
                    h += 1
                lcp[rank[i]] = h
                if h > 0:
                    h -= 1
        return lcp

    # Build suffix array and LCP array
    suffix_array = build_suffix_array(s)
    lcp = build_lcp(s, suffix_array)
    
    # Find the maximum length and its index
    max_len = 0
    index = 0
    for i in range(1, n):
        if lcp[i] > max_len:
            max_len = lcp[i]
            index = suffix_array[i]

    # Return the longest repeating substring
    return s[index:index + max_len]

def check_substring_at_end(s: str, N: int) -> bool:
    """
    Checks if the longest repeating substring in the given string appears near the end of the string.

    Args:
        s (str): The input string to check.
        N (int): The minimum length of the repeating substring to consider for checking at the end.

    Returns:
        bool: True if a significant part of the repeating substring is found at the end of the string, False otherwise.
    """
    # Step 1: Find the longest repeating substring
    longest_repeat = longest_repeating_substring(s)
    
    if not longest_repeat:
        return False  # No repeating substring found
    
    # Step 2: Check if the substring or a substantial part of it is at the end of the string
    for length in range(len(longest_repeat), N - 1, -1):
        if s.endswith(longest_repeat[:length]):
            return True
    
    return False

#We actually need to check this twice, first to see if there is a long repeating substring, then to see if it is at the end
def check_repeating(text: str):
    """
    Checks if there is a repeating substring in the given text and if it appears at the end of the text.

    Args:
        text (str): The input text to check for repeating substrings.

    Returns:
        bool: True if a repeating substring longer than 10 characters is found and part of it appears at the end, False otherwise.
    """
    result = longest_repeating_substring(text.strip())
    if len(result) > 10: #check if the substring is worth investigating
         if(check_substring_at_end(text.strip(),5)): #check if some substring of it occurs at the end
            return True
    return False

prompt = "The image contains a snippet from a report that may have text, tables, or images in it. Convert all text in the image into valid markdown. It is critical that you convert the text faithfully. Do not make anything up. Make sure you convert all text. You must respect the formatting, especially for tabular data and headings."


prompt_repeat = "The image contains a snippet from a report. Convert all text in the image into valid markdown. It is critical that you convert the text faithfully and entirely. Do not make anything up. You must respect the formatting, especially for tabular data and headings."

def process_subimages_from_zip(zip_path: str, prompt_text: str) -> str:
    """
    Processes a ZIP file containing image snippets, extracting text from each image using an API and combining the results into a single string.

    Args:
        zip_path (str): The path to the ZIP file containing image snippets.
        prompt_text (str): The prompt to use when processing the images.

    Returns:
        str: The combined text extracted from all images in the ZIP file.

    Raises:
        ValueError: If no valid image files are found in the ZIP file.
    """

    # Extract the base name of the input file to use as the temp folder name
    base_filename = os.path.splitext(os.path.basename(zip_path))[0]
    
    # Create a temporary directory with the name based on the input file
    temp_dir = tempfile.mkdtemp(prefix=f"{base_filename}_")
    
    try:
        # Unzip the contents of the ZIP file into the temp directory
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Get a list of files and sort them by the numeric part of their names
        files = []
        for root, dirs, filenames in os.walk(temp_dir):
            for filename in filenames:                
                # Extract the number from the filename
                match = re.match(r'text_(\d+)\.jpeg', filename)
                if match:
                    num = int(match.group(1))
                    files.append((num, os.path.join(root, filename)))
        
        # Sort files by the extracted number
        files.sort(key=lambda x: x[0])
        
        # Initialize an empty string to store the combined text
        combined_text = ""

        # Iterate over sorted files
        for _, image_path in files:
            # Call the nebula API to process the image
            text_output = nebula_api_image_text_endpoint(image_path, prompt_text)['response']
            #print(text_output)
            if(check_repeating(text_output)):
                print(f"ERROR with {image_path}. Text is: {text_output}")
                text_output = nebula_api_image_text_endpoint(image_path, prompt_repeat)['response']
            # Append the text to the combined string
            combined_text += text_output + "\n"
        
        return combined_text.strip()  # Return the combined text, removing any trailing newlines
    finally:
        # Clean up: remove the temporary directory and its contents
        shutil.rmtree(temp_dir)

def send_image_and_receive_zip(image_path: str, endpoint: str = "http://ece-nebula11.eng.uwaterloo.ca:8004/process-image/"):
    """
    Sends an image file to a remote server for processing and receives a ZIP file in response.

    Args:
        image_path (str): The path to the image file to send.
        endpoint (str): The URL of the server endpoint to send the image to.

    Returns:
        str: The filename of the received ZIP file. Returns None if the request fails.
    """

    # Open the image file in binary mode
    with open(image_path, "rb") as image_file:
        # Prepare the file for upload
        files = {"file": (image_path, image_file, "image/jpeg")}
        
        # Send the POST request to the server
        response = requests.post(endpoint, files=files)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Save the received ZIP file
            zip_filename = f"{image_path}_subimages.zip"
            with open(zip_filename, "wb") as zip_file:
                zip_file.write(response.content)
            #print(f"ZIP file saved as {zip_filename}")
            return zip_filename
        else:
            # Handle errors
            print(f"Failed to process image. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None

def ocr_pdf(pdf_path, project_name=None, results_dir="ocr",save_to_file=False):
    """
    Performs OCR on a PDF file, converting it to images and extracting text from the images.

    Args:
        pdf_path (str): The path to the PDF file to process.
        project_name (str, optional): The name of the project to use for organizing results. Defaults to the PDF filename.
        results_dir (str, optional): The directory to save the OCR results. Defaults to "ocr".
        save_to_file (bool, optional): Whether to save the extracted text to a file. Defaults to False.

    Returns:
        str: The extracted text from the PDF file.
    """

    # Set up the project and its directories
    if project_name is None:
        project_name = os.path.splitext(os.path.basename(pdf_path))[0]
    project_directory = os.path.join(results_dir, project_name)
    os.makedirs(project_directory, exist_ok=True)
    output_directory = os.path.join(project_directory, "results")
    os.makedirs(output_directory, exist_ok=True)
    
    # Run the extraction
    project = Project(project_name, pdf_path, output_directory)
    project.add_step(PDFToImageConverter, combine_images=False)  # need to operate page by page
    project.run()

    running_text = ""

    # Process each image file in the output directory
    for root, dirs, filenames in os.walk(output_directory):
        # Sort the filenames by the number N extracted from the pattern
        filenames = sorted(filenames, key=lambda x: int(x.rsplit('_', 1)[-1].split('.')[0]))
        
        for filename in filenames:
            if filename.endswith('.jpg'):
                image_path = os.path.join(root, filename)
                zip_path = send_image_and_receive_zip(image_path)
                if zip_path:
                    running_text += "\n" + process_subimages_from_zip(zip_path, prompt).replace("```markdown","").replace("```","")
    if save_to_file == True:
        # Save the combined text to a file in the output directory
        result_file_path = os.path.join(output_directory, f"{project_name}_ocr_results.txt")
        with open(result_file_path, "w") as result_file:
            result_file.write(running_text)
    #Done! Return
    return running_text

# Example usage
for pdf_file in os.listdir("small_pdfs"):
    print(ocr_pdf(os.path.join("small_pdfs",pdf_file),results_dir="small_ocr"))
