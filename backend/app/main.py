"""
C.O.V.E.R.T Backend - Main Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.core.config import settings

# Initialize FastAPI app
app = FastAPI(
    title="C.O.V.E.R.T API",
    description="Chain for Open and VERified Testimonies",
    version="0.1.0",
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# GZip Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


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
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
    }


# Import and include routers (will be added in later phases)
# from app.api import reports, moderation, disputes, reputation
# app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
# app.include_router(moderation.router, prefix="/api/v1/moderation", tags=["moderation"])
# app.include_router(disputes.router, prefix="/api/v1/disputes", tags=["disputes"])
# app.include_router(reputation.router, prefix="/api/v1/reputation", tags=["reputation"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False,
    )
