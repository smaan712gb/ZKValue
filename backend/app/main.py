import logging
import structlog
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.middleware.audit import AuditMiddleware
from app.api.middleware.tenant import RateLimitMiddleware
from app.api.routes import (
    auth, organizations, verifications, credit, ai_ip, dashboard, billing, audit,
    schedules, notifications, analytics, document_ai, model_registry, stress_testing,
    regulatory, blockchain, nl_query,
)

# Configure structured logging — JSON in production, console in development
_is_production = settings.ENVIRONMENT == "production"
_renderer = structlog.processors.JSONRenderer() if _is_production else structlog.dev.ConsoleRenderer()

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        _renderer,
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate required configuration at startup
    settings.validate_required()

    logger.info("Starting ZKValue API", version=settings.APP_VERSION)

    # Initialize Sentry if configured
    if settings.SENTRY_DSN:
        import sentry_sdk
        sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=0.1)

    yield

    logger.info("Shutting down ZKValue API")


app = FastAPI(
    title=settings.APP_NAME,
    description="ZKValue — Cryptographic proof layer for opaque assets. Verifiable computation for alternative asset valuation.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if not _is_production else None,
    redoc_url="/redoc" if not _is_production else None,
    openapi_url="/openapi.json" if not _is_production else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
)

# Rate limiting
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

# Audit logging
app.add_middleware(AuditMiddleware)

# Routes
app.include_router(auth.router, prefix="/api/v1")
app.include_router(organizations.router, prefix="/api/v1")
app.include_router(verifications.router, prefix="/api/v1")
app.include_router(credit.router, prefix="/api/v1")
app.include_router(ai_ip.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(billing.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(schedules.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(document_ai.router, prefix="/api/v1")
app.include_router(model_registry.router, prefix="/api/v1")
app.include_router(stress_testing.router, prefix="/api/v1")
app.include_router(regulatory.router, prefix="/api/v1")
app.include_router(blockchain.router, prefix="/api/v1")
app.include_router(nl_query.router, prefix="/api/v1")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error_code": "INTERNAL_ERROR"},
    )


# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": settings.APP_NAME,
    }


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Cryptographic proof layer for opaque assets",
        "docs": "/docs",
    }
