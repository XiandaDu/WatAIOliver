from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from src.api import register_routes

# Qwen model endpoint (from legacy uw_llm.py)
import sys
import os

# Add the project root to the path so we can import config
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.constants import ServiceConfig

BASE_URL = ServiceConfig.NEBULA_BASE_URL

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