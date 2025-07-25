# PDF Processor

This service converts uploaded PDFs to text. The instructions below cover macOS, Linux and Windows.

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

Then open `http://localhost:8001/docs` in your browser, upload a PDF to `/convert`, and check the output folder `pdf_processor/output`.