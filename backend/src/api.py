from fastapi import FastAPI
from src.auth.router import router as auth_router
from src.chat.router import router as chat_router
from src.course.router import router as course_router
from src.user.router import router as user_router
from src.file.router import router as file_router
from src.conversationTable.router import router as conversation_router
from src.documents.router import router as documents_router
from src.messages.router import router as messages_router

def register_routes(app: FastAPI):
    app.include_router(auth_router)
    app.include_router(chat_router)
    app.include_router(course_router)
    app.include_router(user_router)
    app.include_router(file_router)
    app.include_router(conversation_router)
    app.include_router(documents_router)
    app.include_router(messages_router)