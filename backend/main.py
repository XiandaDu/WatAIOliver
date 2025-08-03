from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

from src.log_middleware import LoggingMiddleware
import os

from src.api import register_routes

# Load environment variables from backend .env file
backend_env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(backend_env_path)

app = FastAPI(title="WatAI Oliver Backend", version="1.0.0")

app.add_middleware(LoggingMiddleware)

# Enable CORS for all origins (development only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session management
session_secret_key = os.getenv("SESSION_SECRET_KEY")
if not session_secret_key:
    raise ValueError("SESSION_SECRET_KEY environment variable is required but not set in backend .env")

app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret_key,
    max_age=3600,
)

register_routes(app)

@app.get("/")
async def root():
    return {"message": "WatAI Oliver Backend", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
