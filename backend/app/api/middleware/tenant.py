import time
import logging
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Public paths that don't require authentication
PUBLIC_PATHS = {
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/invite/accept",
    "/api/v1/billing/webhook",
}


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip public paths
        if path in PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        # The actual tenant isolation is handled by the deps.py get_current_user
        # This middleware adds the org context to the request state for logging
        response = await call_next(request)
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory rate limiting middleware per IP address.

    For production with multiple workers, replace with Redis-backed rate limiting.
    """

    def __init__(self, app, requests_per_minute: int = 300):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self._request_log: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for webhooks and health checks
        path = request.url.path
        if path in ("/health", "/api/v1/billing/webhook"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - 60

        # Clean old entries and add current request
        self._request_log[client_ip] = [
            ts for ts in self._request_log[client_ip] if ts > window_start
        ]

        if len(self._request_log[client_ip]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
                headers={"Retry-After": "60"},
            )

        self._request_log[client_ip].append(now)
        response = await call_next(request)
        return response
