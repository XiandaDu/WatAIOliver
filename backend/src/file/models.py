from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime

class FileBase(BaseModel):
    user_id: str
    file_name: str
    file_type: str
    file_size: int
    file_path: str
