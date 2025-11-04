from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

import os
import logging

from exceptions import ComputationError, MissingParameterError, ParseError
from model import ComputeRequest
from service import CalculatorService
from service.validator import validate_expression

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


@app.get("/health")
async def health():
    """Health check endpoint"""
    logger.debug("Health check requested")
    return {"status": "healthy"}


@app.post("/compute")
async def compute(request: ComputeRequest):
    """Execute mathematical computation"""
    logger.info(
        f"Compute request received: mode={request.mode}, expr={request.expr[:50]}..."
    )

    # validate expression
    is_valid, error_message = validate_expression(request.expr)
    if not is_valid:
        logger.warning(f"Invalid expression: {error_message}")
        raise HTTPException(status_code=422, detail=error_message)

    # compute
    try:
        service = CalculatorService()
        result = service.compute(request)

        if result["ok"]:
            logger.info(
                f"Computation successful: mode={request.mode}, result_type={type(result['result']).__name__}"
            )
        else:
            logger.warning(f"Computation failed: {result['result']}")

        return result

    except TimeoutError as e:
        logger.error(f"Computation timeout: {str(e)}")
        raise HTTPException(status_code=400, detail="Operation timed out")
    except ParseError as e:
        logger.error(f"Parse error: {str(e)}")
        raise HTTPException(status_code=400, detail="Expression parsing failed")
    except MissingParameterError as e:
        logger.error(f"Missing parameter: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except ComputationError as e:
        logger.error(f"Computation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
