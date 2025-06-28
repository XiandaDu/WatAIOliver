from fastapi import FastAPI
from src.chat.router import router as chat_router
from src.course.router import router as course_router
from src.user.router import router as user_router
from src.file.router import router as file_router
from src.conversationTable.router import router as conversation_router

def register_routes(app: FastAPI):
    app.include_router(chat_router)
    app.include_router(course_router)
    app.include_router(user_router)
    app.include_router(file_router)
    app.include_router(conversation_router)