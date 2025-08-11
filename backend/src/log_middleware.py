from starlette.middleware.base import BaseHTTPMiddleware
from time import time
from starlette.requests import Request
from starlette.responses import Response

from .logger import logger

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time()
        logger.info(f"{request.method} {request.url.path}")
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.exception("Unhandled error: %s", exc)
            raise
        duration = time() - start
        logger.info(
            f"{response.status_code} {request.url.path} - {duration:.2f}s"
        )
        return response
