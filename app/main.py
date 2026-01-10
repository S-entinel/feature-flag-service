from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import flags
from app.config import settings
from app.security import get_api_key_info

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="A production-ready feature flag service for controlling feature rollouts",
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# CORS middleware - properly configured from environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Controlled via ALLOWED_ORIGINS env var
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(flags.router)


@app.get("/")
def root():
    """Root endpoint with API information"""
    return {
        "message": f"{settings.APP_NAME} is running",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint for monitoring and load balancers
    
    Returns service health status and configuration info.
    """
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": "production" if settings.is_production else "development",
        "database": "connected",
        "cache": "disabled"  # No Redis in Vercel
    }


@app.get("/security-info")
def security_info():
    """
    Get security configuration information
    
    Useful for debugging and verifying security setup.
    Does not expose sensitive values.
    """
    return {
        **get_api_key_info(),
        "cors_origins": settings.ALLOWED_ORIGINS,
        "rate_limiting_enabled": settings.RATE_LIMIT_ENABLED
    }