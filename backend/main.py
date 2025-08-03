from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import register_routes

app = FastAPI(title="WatAI Oliver Auth Backend", version="1.0.0")

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

@app.get("/")
async def root():
    return {"message": "WatAI Oliver Authentication Backend"}

@app.get("/health")
async def health() -> dict:
    """Basic health check endpoint."""
    return {"status": "ok"} 