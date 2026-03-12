import logging
from datetime import datetime, timezone
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)

# Paths to skip auditing
SKIP_AUDIT_PATHS = {"/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico"}


class AuditMiddleware(BaseHTTPMiddleware):
    """Log all API calls to audit log for compliance."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path in SKIP_AUDIT_PATHS:
            return await call_next(request)

        # Log the request
        logger.info(
            "api_request",
            extra={
                "method": request.method,
                "path": path,
                "ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", ""),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        response = await call_next(request)

        # Log the response
        logger.info(
            "api_response",
            extra={
                "method": request.method,
                "path": path,
                "status_code": response.status_code,
            },
        )

        return response
