from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime


class ComputeResponse(BaseModel):
    ok: bool = Field(..., description="Whether the operation was successful")
    result: Any = Field(
        ..., description="The computation result or error message (JSON serializable)"
    )
    mode: Optional[str] = Field(
        None, description="The requested computation mode (for debugging)"
    )
    timestamp: datetime = Field(..., description="The response timestamp")
