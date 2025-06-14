from fastapi import FastAPI
from src.chat.router import router as chat_router

def register_routes(app: FastAPI):
    app.include_router(chat_router)