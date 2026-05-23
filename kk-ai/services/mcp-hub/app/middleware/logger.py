"""Logger middleware: Structured JSON logging with trace_id, latency, status."""

import json
import logging
import time
import uuid
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.config import get_settings

logger = logging.getLogger("mcp-hub.access")


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra"):
            log_obj.update(record.extra)
        return json.dumps(log_obj, default=str, ensure_ascii=False)


def setup_logging() -> None:
    """Configure structured JSON logging."""
    settings = get_settings()
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    handler = logging.StreamHandler()
    if settings.LOG_FORMAT == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )

    root_logger = logging.getLogger("mcp-hub")
    root_logger.setLevel(level)
    root_logger.handlers = []
    root_logger.addHandler(handler)

    # Also configure uvicorn loggers
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers = []
        uvicorn_logger.addHandler(handler)
        uvicorn_logger.setLevel(level)


class LoggerMiddleware(BaseHTTPMiddleware):
    """
    Outer-most middleware:
    - Generates trace_id for every request
    - Records start time
    - Logs structured JSON on response with latency, status, project_id
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        trace_id = request.headers.get("X-Trace-Id", str(uuid.uuid4()))
        request.state.trace_id = trace_id

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception as exc:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Unhandled exception",
                extra={
                    "trace_id": trace_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": 500,
                    "latency_ms": round(latency_ms, 3),
                    "error": str(exc),
                    "project_id": getattr(request.state, "project_id", None),
                },
            )
            raise

        latency_ms = (time.perf_counter() - start_time) * 1000
        status_code = response.status_code

        # Add trace_id to response headers
        response.headers["X-Trace-Id"] = trace_id

        # Add quota headers if available
        quota_info = getattr(request.state, "quota_info", None)
        if quota_info:
            response.headers["X-Quota-Daily-Used"] = str(quota_info["daily_used"])
            response.headers["X-Quota-Daily-Limit"] = str(quota_info["daily_limit"])
            response.headers["X-Quota-Monthly-Used"] = str(quota_info["monthly_used"])
            response.headers["X-Quota-Monthly-Limit"] = str(quota_info["monthly_limit"])

        log_data = {
            "trace_id": trace_id,
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params),
            "status": status_code,
            "latency_ms": round(latency_ms, 3),
            "project_id": getattr(request.state, "project_id", None),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }

        if status_code >= 500:
            logger.error("Request completed", extra=log_data)
        elif status_code >= 400:
            logger.warning("Request completed", extra=log_data)
        else:
            logger.info("Request completed", extra=log_data)

        return response
