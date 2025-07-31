from fastapi import FastAPI
from src.api import register_routes
from starlette.middleware.sessions import SessionMiddleware

from src.log_middleware import LoggingMiddleware

app = FastAPI()

app.add_middleware(LoggingMiddleware)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health() -> dict:
    """Basic health check endpoint."""
    return {"status": "ok"}

register_routes(app)