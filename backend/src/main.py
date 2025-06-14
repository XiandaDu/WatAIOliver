from fastapi import FastAPI
from .api import register_routes
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()

# Add session middleware to handle user sessions (e.g., login sessions)
app.add_middleware(SessionMiddleware, secret_key="your_secret_key",
                   max_age=3600)

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health() -> dict:
    """Basic health check endpoint."""
    return {"status": "ok"}

register_routes(app)