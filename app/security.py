"""
Security utilities for API authentication and authorization
"""

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from typing import Optional

from app.config import settings


# API Key header scheme
api_key_header = APIKeyHeader(
    name=settings.API_KEY_HEADER,
    auto_error=False  # We'll handle errors manually for better messages
)


async def verify_api_key(
    api_key: Optional[str] = Security(api_key_header)
) -> str:
    """
    Verify API key for protected endpoints
    
    This dependency should be added to endpoints that modify data:
    - Creating flags
    - Updating flags  
    - Deleting flags
    
    Read-only endpoints (evaluating flags) should remain public for performance.
    
    Args:
        api_key: API key from request header
        
    Returns:
        The validated API key
        
    Raises:
        HTTPException: If API key is missing or invalid
    """
    # If no API key is configured, allow all requests
    # This is for development/demo purposes only
    if settings.API_KEY is None:
        return "development"
    
    # Check if API key was provided
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "missing_api_key",
                "message": f"API key required. Provide via '{settings.API_KEY_HEADER}' header."
            },
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Validate API key
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "invalid_api_key",
                "message": "Invalid API key provided."
            }
        )
    
    return api_key


# Optional: Create a dependency that only checks API key if configured
async def verify_api_key_optional(
    api_key: Optional[str] = Security(api_key_header)
) -> Optional[str]:
    """
    Verify API key only if authentication is enabled
    
    This allows for graceful degradation in development.
    """
    if settings.API_KEY is None:
        return None
    
    return await verify_api_key(api_key)


def get_api_key_info() -> dict:
    """
    Get information about API key configuration
    
    Useful for health checks and debugging.
    """
    return {
        "authentication_enabled": settings.API_KEY is not None,
        "api_key_header": settings.API_KEY_HEADER,
        "environment": "production" if settings.is_production else "development"
    }