import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

import os
import logging

from exceptions import (
    CalculatorError,
    ComputationError,
    MissingParameterError,
    ParseError,
    ComputationTimeoutError,
)
from model import ComputeRequest, ComputeResponse
from service import CalculatorService
from service.validator import validate_expression
from utils import serialize_result

# Configure logging to stdout (for container logging systems)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],  # Output to stdout
)

# Suppress noisy library logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("sympy").setLevel(logging.WARNING)

# Get logger for this module
logger = logging.getLogger("calculator_service")

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
    """Root endpoint with service information"""
    logger.info("Root endpoint accessed")
    return {"message": "WatAI Oliver Calculator Service", "status": "running"}


# TODO: implement health check
@app.get("/health")
async def health():
    """Health check endpoint"""
    logger.debug("Health check requested")
    return {"status": "healthy"}


# TODO: implement automatic restart policies.
@app.post("/v1/compute")
async def compute(request: ComputeRequest):
    """Execute mathematical computation"""
    logger.info(
        f"Compute request received: mode={request.mode}, expr={request.expr[:50]}..."
    )

    try:

        is_valid, error_message = validate_expression(request.expr)
        if not is_valid:
            logger.error(f"Invalid expression: {error_message}")
            raise ParseError(error_message)

        if request.lower is not None:
            is_valid, error_message = validate_expression(request.lower)
            if not is_valid:
                logger.error(f"Invalid lower bound: {error_message}")
                raise ParseError(error_message)

        if request.upper is not None:
            is_valid, error_message = validate_expression(request.upper)
            if not is_valid:
                logger.error(f"Invalid upper bound: {error_message}")
                raise ParseError(error_message)

        service = CalculatorService()
        result = service.compute(request)

        if result["ok"]:
            result["result"] = serialize_result(result["result"], request.mode)
            logger.info(
                f"Computation successful: mode={request.mode}, result_type={type(result['result']).__name__}"
            )
        else:
            logger.error(f"Computation failed: {result['result']}")
            raise ComputationError(result["result"])

        return ComputeResponse(
            ok=result["ok"],
            result=result["result"],
            mode=request.mode,
            timestamp=datetime.datetime.now(),
        )

    # handle errors
    except CalculatorError as e:
        # map error type to status code
        if isinstance(e, (ParseError, MissingParameterError)):
            status_code = 422
        elif isinstance(e, (ComputationError, ComputationTimeoutError)):
            status_code = 400
        else:
            status_code = 500

        logger.error(f"{e.__class__.__name__}: {str(e)}")
        raise HTTPException(
            status_code=status_code,
            detail={
                "ok": False,
                "result": str(e),
                "mode": request.mode,
                "timestamp": datetime.datetime.now().isoformat(),
            },
        )

    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={
                "ok": False,
                "result": str(e),
                "mode": request.mode,
                "timestamp": datetime.datetime.now().isoformat(),
            },
        )
