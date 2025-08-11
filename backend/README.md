# Backend

The backend is built with FastAPI and provides the main chat and file upload APIs. It also coordinates with the RAG system and optional agent services.

## Setup

Create a Python 3.9+ virtual environment and install dependencies:
```bash
pip install -r requirements.txt
```

Run the development server:
```bash
PYTHONPATH=backend python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
The interactive docs are available at [http://localhost:8000/docs](http://localhost:8000/docs).

On Linux or macOS the same command works. The Windows example below shows the equivalent using `set`.

### Windows Example

```bat
set PYTHONPATH=backend
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Logs are written to `src/app.log` with rotation. Each request records its method, path and duration.
