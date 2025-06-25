from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import zipfile
import mimetypes
from fastapi.responses import FileResponse
from typing import List
import shutil
import os
from typing import List
from extractapi import *
from evaluateapi import * #TODO: makethese pip installable
import csv

app = FastAPI()
templates = Jinja2Templates(directory="templates")



def get_original_filename(filename):
    # Extracts the original filename from the text file's name
    return filename.split('_')[0] + '.pdf'

def output_document_report(output_folder, csv_path):
    # Option 1: Create a CSV with a "yes" or "no" if any file contains "yes"
    data = {}
    
    for filename in os.listdir(output_folder):
        if filename.endswith('.txt'):
            original_filename = get_original_filename(filename)
            with open(os.path.join(output_folder, filename), 'r') as file:
                content = file.read()
                if "yes" in content.lower():
                    data[original_filename] = "yes"
                elif original_filename not in data:
                    data[original_filename] = "no"
    
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Original Filename', 'At least one matching page?'])
        for original_filename, contains_yes in data.items():
            writer.writerow([original_filename, contains_yes])

def output_page_report(output_folder, csv_path):
    # Option 2: Create a CSV with all file contents as separate columns
    data = {}
    
    for filename in os.listdir(output_folder):
        if filename.endswith('.txt'):
            original_filename = get_original_filename(filename)
            with open(os.path.join(output_folder, filename), 'r') as file:
                content = file.read()
                if original_filename not in data:
                    data[original_filename] = []
                data[original_filename].append(content)
    
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        max_columns = max(len(contents) for contents in data.values())
        header = ['Original Filename'] + [f'Page {i+1}' for i in range(max_columns)]
        writer.writerow(header)
        
        for original_filename, contents in data.items():
            row = [original_filename] + contents
            writer.writerow(row)

def get_all_matching_subfiles(output_folder,pdf_folder, pages_directory, search_string):
    # Option 3: Search for a string and create new folders with matching splits
    for filename in os.listdir(output_folder):
        if filename.endswith('.txt'):
            original_filename = get_original_filename(filename)
            with open(os.path.join(output_folder, filename), 'r') as file:
                content = file.read()
                if search_string.lower() in content.lower():
                    # Extract the split number using regex
                    match = re.search(r'_split_(\d+)', filename)
                    if match:
                        split_num = match.group(1)
                        original_file_stem = filename.split('_split_')[0]
                        pdf_filename = f'{original_file_stem}_split_{split_num}.pdf'
                        source_path = os.path.join(pages_directory, original_file_stem, pdf_filename)
                        
                        target_directory = os.path.join(pdf_folder, original_filename)
                        os.makedirs(target_directory, exist_ok=True)
                        target_path = os.path.join(target_directory, pdf_filename)
                        
                        if os.path.exists(source_path):
                            shutil.copy2(source_path, target_path)
                            
    #Really now there should be a zip file created...
                            
def run_convergence(output_folder, convergence_folder, pages_directory, options, search_string=None):
    # Execute selected convergence options
    os.makedirs(convergence_folder, exist_ok=True)
    csv_folder = os.path.join(convergence_folder,'csvs')
    pdf_folder = os.path.join(convergence_folder,'pdfs')
    if 1 in options:
        os.makedirs(os.path.join(convergence_folder,'csvs'), exist_ok=True)
        output_document_report(output_folder, os.path.join(csv_folder, 'convergence_1.csv'))
    
    if 2 in options:
        output_page_report(output_folder, os.path.join(csv_folder, 'convergence_2.csv'))
    
    if 3 in options and search_string:
        os.makedirs(os.path.join(convergence_folder,'pdfs'), exist_ok=True)
        get_all_matching_subfiles(output_folder,pdf_folder, pages_directory, search_string)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/run")
async def run(
    request: Request,
    project_name: str = Form(...),
    question: str = Form(...),
    zip_file: UploadFile = File(...),
    options: List[str] = Form(...)
    ):
    
    # Validate that at least one option is selected
    if not options:
        return templates.TemplateResponse("index.html", {"request": request, "error": "At least one option must be selected"})

    # Save the uploaded zip file
    file_location = f"uploads/{zip_file.filename}"
    os.makedirs("uploads", exist_ok=True)
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(zip_file.file, file_object)

    # Process the data
    input_file = file_location
    project_directory = project_name
    output_directory = os.path.join(project_directory, "out")
    results_path = os.path.join(output_directory, "results")
    
    # Save the question as prompt
    prompt_path = os.path.join(project_directory, "prompt.txt")
    os.makedirs(project_directory, exist_ok=True)
    with open(prompt_path, "w") as f:
        f.write(question)

    project = Project(project_name, input_file, output_directory)
    pdf_files_directory = project.add_step(ZipExtractor)
    pages_directory = project.add_step(PagePdfSplitter, pages_per_split=1)
    project.add_step(Converger, 'converge')
    project.add_step(PDFToImageConverter, 'flat')
    images_out = project.add_step(Converger, 'converge')
    project.run()

    documents_path = images_out
    prompts = [prompt_path]
    output_path = f"{output_directory}/results"
    evaluator_evals = ImageToTextEvaluator(documents_path, prompts, output_path)
    evaluator_evals.run_evaluation()
    print(options)
    # Convert options to integers and filter for 1, 2, 3
    options = [int(opt.replace("option", "")) for opt in options if opt.replace("option", "") in ['1', '2', '3']]
  
    search_string = 'yes'  # The string to search for in option 3

    convergence_output = os.path.join(output_directory,"converged")
    
    run_convergence(output_path,convergence_output, pages_directory, options, search_string)
    
    #now let's extract the images
    process_project_name = "processed"
    input_directory = os.path.join(convergence_output,"pdfs")
    process_project_directory = os.path.join(project_name,process_project_name)
    process_project = Project(process_project_name,input_directory,process_project_directory)
    processed_pages_directory = process_project.add_step(Converger,'converge')
    folder_images_directory = process_project.add_step(PDFToImageConverter,'flat')
    images_directory = process_project.add_step(Converger,'converge')
    process_project.run()

    result = f"Processing complete for project '{project_name}' with options: {', '.join(map(str, options))}."
    return templates.TemplateResponse("index.html", {"request": request, "result": result, "project_name": project_name})

@app.get("/images/{project_name}")
async def get_images(project_name: str):
    image_dir = f"{project_name}/processed/step_3"
    images = [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    return {"images": images}

@app.get("/image/{project_name}/{image_name}")
async def get_image(project_name: str, image_name: str):
    image_path = f"{project_name}/processed/step_3/{image_name}"
    return FileResponse(image_path)

@app.get("/download/{project_name}")
async def download_images(project_name: str):
    image_dir = f"{project_name}/processed/step_3"
    zip_path = f"{project_name}/images.zip"
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, dirs, files in os.walk(image_dir):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    zipf.write(os.path.join(root, file), file)
    
    return FileResponse(zip_path, filename="images.zip")
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
