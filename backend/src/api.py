from fastapi import FastAPI
from src.chat.router import router as chat_router
from src.course.routers import router as course_router

def register_routes(app: FastAPI):
    app.include_router(chat_router)
    app.include_router(course_router)