"""
C.O.V.E.R.T Backend - Main Application Entry Point
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import init_db, close_db, engine


# ── Rate limiter (backed by Redis when REDIS_URL is set) ────────────────────
# Privacy note: IP addresses are used transiently for rate-limit buckets only.
# They are NEVER logged, stored in the database, or included in API responses.
def _get_limiter_key(request: Request) -> str:
    """Use the authenticated wallet address if available, otherwise fall back to IP."""
    wallet = request.headers.get("X-Wallet-Address")
    if wallet:
        return wallet.lower()
    return get_remote_address(request)


_storage_uri = settings.REDIS_URL if settings.REDIS_URL else "memory://"
limiter = Limiter(key_func=_get_limiter_key, storage_uri=_storage_uri)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    import logging
    logging.getLogger(__name__).info(f"CORS_ORIGINS: {settings.CORS_ORIGINS}")
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


# Initialize FastAPI app
app = FastAPI(
    title="C.O.V.E.R.T API",
    description="Chain for Open and VERified Testimonies",
    version="0.1.0",
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

# Attach limiter to app state so route decorators can find it
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "X-Wallet-Address"],
)

# GZip Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Global exception handler — ensures unhandled 500s still return a proper
# JSON response so the CORS middleware can attach its headers.
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import logging
    logging.getLogger(__name__).error(f"Unhandled error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "C.O.V.E.R.T API",
        "version": "0.1.0",
        "status": "online",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint — verifies critical dependencies"""
    checks = {"environment": settings.ENVIRONMENT}

    # Database
    try:
        from sqlalchemy import text as sa_text
        async with engine.begin() as conn:
            await conn.execute(sa_text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "unreachable"

    # Overall status
    all_ok = checks.get("database") == "ok"
    checks["status"] = "healthy" if all_ok else "degraded"
    status_code = 200 if all_ok else 503
    from fastapi.responses import JSONResponse
    return JSONResponse(content=checks, status_code=status_code)


# Import and include routers
from app.api.v1 import auth, reports, moderation, reputation, zkp, ai_analysis, dms, moderation_notes, dev, routing

app.include_router(auth.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(moderation.router, prefix="/api/v1")
app.include_router(reputation.router, prefix="/api/v1")
app.include_router(zkp.router, prefix="/api/v1")
app.include_router(ai_analysis.router, prefix="/api/v1")
app.include_router(dms.router, prefix="/api/v1")
app.include_router(moderation_notes.router, prefix="/api/v1")
app.include_router(routing.router, prefix="/api/v1")
if settings.DEBUG and settings.ENVIRONMENT == "development":
    app.include_router(dev.router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False,
    )
