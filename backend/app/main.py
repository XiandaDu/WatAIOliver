from fastapi import FastAPI
from app.api import conversation, test

app = FastAPI()
app.include_router(conversation.router)
app.include_router(test.router)