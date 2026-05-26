"""Project ID validation middleware."""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse


class ProjectAuthMiddleware(BaseHTTPMiddleware):
    """
    Validates X-Project-Id header for multi-tenant isolation.
    Skips for health endpoints.
    """

    EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        path = request.url.path

        if any(path.startswith(ep) for ep in self.EXEMPT_PATHS):
            return await call_next(request)

        project_id = request.headers.get("X-Project-Id")
        if not project_id:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "MISSING_PROJECT_ID",
                    "message": "Missing X-Project-Id header",
                },
            )

        # Attach to request state
        request.state.project_id = project_id
        return await call_next(request)
