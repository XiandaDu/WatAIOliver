from fastapi import APIRouter, Request, UploadFile, File, Form, Query, HTTPException, status
from . import service

router = APIRouter(
    prefix='/user',
    tags=['user']
)

@router.get("/")
# used to be "get_current_user" 
async def get_user_info():
    return service.get_user_info() 

@router.get("/login")
async def login():
    return service.login()

@router.get("/logout")
async def logout():
    return service.logout()






