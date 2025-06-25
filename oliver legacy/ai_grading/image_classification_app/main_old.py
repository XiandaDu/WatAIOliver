from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from extract_api import *
from evaluate_api import *
import os
import shutil
import zipfile

app = FastAPI()

# Set up static and template directories
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Home page with form for user inputs
@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Endpoint to process the form submission
@app.post("/process")
async def process_form(
    request: Request,
    project_name: str = Form(...),
    preamble: str = Form(...),
    categories: str = Form(...),
    file: UploadFile = File(...)
):
    # Set up project directories
    project_directory = os.path.join("temp", project_name)
    output_directory = os.path.join(project_directory, "out")
    results_path = os.path.join(output_directory, "results")
    prompt_path = os.path.join(project_directory, "prompt.txt")

    # Create necessary directories
    os.makedirs(project_directory, exist_ok=True)
    os.makedirs(output_directory, exist_ok=True)
    os.makedirs(results_path, exist_ok=True)

    # Save uploaded zip file
    input_file_path = os.path.join(project_directory, file.filename)
    with open(input_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Save prompt to file
    with open(prompt_path, "w") as prompt_file:
        prompt_file.write(f"PREAMBLE: {preamble}\n")
        for category in categories.split(","):
            prompt_file.write(f"CATEGORY: {category.strip()}\n")

    # Run the extraction and evaluation process
    project = Project(project_name, input_file_path, output_directory)
    pdf_files_directory = project.add_step(ZipExtractor)
    images_directory = project.add_step(ImageSplitter)
    images_out = project.add_step(Converger, 'converge')
    project.run()

    prompts = [prompt_path]
    evaluator_evals = ImageClassificationEvaluator(images_out, prompts, results_path)
    evaluator_evals.run_evaluation()

    # Zip the results directory
    zip_filename = f"{project_name}_results.zip"
    zip_filepath = os.path.join(project_directory, zip_filename)
    shutil.make_archive(base_name=os.path.splitext(zip_filepath)[0], format="zip", root_dir=results_path)

    # Provide the download link
    return templates.TemplateResponse("index.html", {"request": request, "download_link": zip_filename})

# Endpoint to download the results zip file
@app.get("/download/{file_path}")
async def download_file(file_path: str):
    file_location = os.path.join("temp", file_path)
    return FileResponse(path=file_location, media_type='application/zip', filename=file_path)
