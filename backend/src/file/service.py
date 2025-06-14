from fastapi import Depends, FastAPI, Request, UploadFile, File, Form, Query, HTTPException, status
from .models import FileUpload
import pymupdf4llm
import shutil

def upload_file(data: FileUpload):
    # collection_name = f"collection_{id}"
    # collection = collection_new(collection_name)
    # # Define allowed content types and extensions for uploaded files
    # allowed_content_types = ['application/pdf', 'text/plain']
    # allowed_extensions = ['pdf', 'txt', 'tex']

    # file_list = []
    # for file in files:
    #     content_type = file.content_type
    #     filename = file.filename
    #     file_extension = filename.split('.')[-1].lower()
    #     # Validate file type
    #     if content_type not in allowed_content_types and \
    #             file_extension not in allowed_extensions:
    #         continue

    #     file_path = 'uploads/' + filename
    #     # Save uploaded file to the server
    #     with open(file_path, "wb") as buffer:
    #         shutil.copyfileobj(file.file, buffer)

    #     file_list.append('/uploads/' + filename)

    #     text_content = ''
    #     # Extract text content from the file (PDF or text)
    #     if content_type == 'application/pdf' or file_extension == 'pdf':
    #         text_content = ingest_pdf(file_path, print_output=False)
    #     elif content_type == 'text/plain' or file_extension in ['txt', 'tex']:
    #         with open(file_path, 'r', encoding='utf-8') as f:
    #             text_content = f.read()

    #     if text_content.strip():
    #         # Add the extracted content to ChromaDB for later retrieval
    #         add_to_chroma(text_content, filename, collection)
    #     else:
    #         raise ValueError("Text file is empty or invalid.")
    # # Update the Course record in the database with the uploaded file paths
    # db.query(Course).filter(Course.id == id).update(
    #     {"doc": ','.join(file_list)})
    # db.commit()

    # d = {"url": ','.join(file_list)}

    # return ok(data=d)
    pass

def ingest_pdf(file_path, print_output=False):
    md_text = pymupdf4llm.to_markdown(file_path)
    if print_output:
        print(md_text)
    return md_text
