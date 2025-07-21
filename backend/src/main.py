from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from utils.config import ServiceConfig

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


from routes import (
    conversations,
    course_models,
    courses,
    document_embeddings,
    messages,
    models as llm_models,
    users,
)


# Register all routes from api.py
def register_routes(app: FastAPI):
    app.include_router(conversations.router)
    app.include_router(course_models.router)
    app.include_router(courses.router)
    app.include_router(document_embeddings.router)
    app.include_router(messages.router)
    app.include_router(llm_models.router)
    app.include_router(users.router)


# Register all routes from api.py
register_routes(app)
