# Universal Document Processor

This service converts uploaded documents (PDF, images, text files) to markdown using Gemini AI. The instructions below cover macOS, Linux and Windows.

## 1. Install Python 3.10+

- **macOS:** `brew install python@3.10`
- **Ubuntu/Debian:** `sudo apt-get install python3.10 python3.10-venv`
- **Windows:** Download and install from [python.org](https://www.python.org/downloads/).

## 2. Setup virtual environment

```bash
cd pdf_processor
python3.10 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Run the server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

Then open `http://localhost:8001/docs` in your browser, upload any supported document (PDF, PNG, JPG, TXT, MD, etc.) to `/convert`, and check the output folder `pdf_processor/output`.

## Supported Formats

- **PDF files**: Converted to images then processed with Gemini AI
- **Image files**: PNG, JPG, JPEG, GIF, BMP, TIFF, WEBP - processed with Gemini AI  
- **Text files**: TXT, MD, MDX - returned as-is (no AI processing needed)

## Environment Variables

Make sure to set your `GEMINI_API_KEY` in the `.env` file in the `machine_learning` directory.