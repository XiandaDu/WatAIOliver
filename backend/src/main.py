from fastapi import FastAPI
from .api import register_routes

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health() -> dict:
    """Basic health check endpoint."""
    return {"status": "ok"}

register_routes(app)