"""Request logging middleware."""

import logging
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("service-data.access")


class LoggerMiddleware(BaseHTTPMiddleware):
    """Log incoming requests and responses."""

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        logger.info(
            "%s %s - %s - %.3fs",
            request.method,
            request.url.path,
            response.status_code,
            duration,
        )
        return response
