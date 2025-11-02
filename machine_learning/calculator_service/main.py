from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

import os

from exceptions import ComputationError, MissingParameterError, ParseError
from model import ComputeRequest
from service import CalculatorService
from service.validator import validate_expression


# Load environment variables from backend .env file
calculator_service_env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(calculator_service_env_path)

app = FastAPI(title="WatAI Oliver Calculator Service", version="1.0.0")

# Enable CORS for all origins (development only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "WatAI Oliver Calculator Service", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/compute")
async def compute(request: ComputeRequest):
    # validate expression
    is_valid, error_message = validate_expression(request.expr)
    if not is_valid:
        raise HTTPException(status_code=422, detail=error_message)


    # compute
    try:
        service = CalculatorService()
        result = service.compute(request)
        return result

    except TimeoutError as e:
        raise HTTPException(status_code=400, detail="Operation timed out")
    except ParseError as e:
        raise HTTPException(status_code=400, detail="Expression parsing failed")
    except MissingParameterError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ComputationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
