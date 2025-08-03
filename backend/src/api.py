from fastapi import FastAPI
from src.user.router import router as user_router
from src.gmailAuth.router import router as gauth_router
from src.emailAuth.router import router as email_auth_router

def register_routes(app: FastAPI):
    app.include_router(user_router)
    app.include_router(gauth_router)
    app.include_router(email_auth_router)