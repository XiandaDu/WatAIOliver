from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from src.api import register_routes

# Qwen model endpoint (from legacy uw_llm.py)
BASE_URL = "http://ece-nebula07.eng.uwaterloo.ca:8976"

app = FastAPI()

# Allow CORS for local frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routes from api.py
register_routes(app) 