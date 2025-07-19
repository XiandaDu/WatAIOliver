from fastapi import FastAPI, Request, Response
from src.api import register_routes
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()

# Add session middleware to handle user sessions (e.g., login sessions)
app.add_middleware(SessionMiddleware, secret_key="your_secret_key",
                   max_age=3600)

# Added middleware to add headers to all requests
@app.middleware("http")
async def add_custom_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health() -> dict:
    """Basic health check endpoint."""
    return {"status": "ok"}

register_routes(app)