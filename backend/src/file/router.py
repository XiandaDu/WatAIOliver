from fastapi import APIRouter
from . import service
from .models import FileUpload

router = APIRouter(
    prefix='/file',
    tags=['file']
)

@router.post("/upload")
async def upload_file(data: FileUpload):
    return service.upload_file(data)