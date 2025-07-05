# Backend Setup

## Install Dependencies

Ensure you have Python 3.9+ and a virtual environment activated. Then install all required packages:

```bash
pip install -r requirements.txt
```

## Launch the Development Server

Navigate to the project root and start the FastAPI server with hot-reloading enabled:

```bash
uvicorn src.main:app --reload
```

The API will be available at: [http://localhost:8000](http://localhost:8000)
You may run [http://localhost:8000/docs](http://localhost:8000/docs) to see fastapi generated documentations. 