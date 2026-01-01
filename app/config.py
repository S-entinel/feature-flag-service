"""
Configuration management for Feature Flag Service

All configuration values should be set via environment variables.
Defaults are provided for development but should be overridden in production.
"""

import os
from typing import List, Optional
from functools import lru_cache


class Settings:
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Feature Flag Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./feature_flags.db"
    )
    
    # Redis Cache
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes default
    
    # CORS - Security Critical!
    # In production, set ALLOWED_ORIGINS to your actual frontend domain
    # Example: ALLOWED_ORIGINS=https://myapp.com,https://admin.myapp.com
    ALLOWED_ORIGINS: List[str] = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:3001"  # Development defaults
    ).split(",")
    
    # API Security
    # Set this to a strong random string in production
    # Example: openssl rand -hex 32
    API_KEY: Optional[str] = os.getenv("API_KEY")  # None = authentication disabled
    API_KEY_HEADER: str = "X-API-Key"
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    WORKERS: int = int(os.getenv("WORKERS", "1"))
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return os.getenv("ENVIRONMENT", "development").lower() == "production"
    
    @property
    def sqlalchemy_connect_args(self) -> dict:
        """Get SQLAlchemy connection arguments based on database type"""
        if "sqlite" in self.DATABASE_URL:
            return {"check_same_thread": False}
        return {}
    
    def validate(self):
        """Validate critical configuration on startup"""
        errors = []
        
        # Check for production security issues
        if self.is_production:
            if self.API_KEY is None:
                errors.append(
                    "⚠️  WARNING: API_KEY not set in production! "
                    "API endpoints are unprotected."
                )
            
            if "*" in self.ALLOWED_ORIGINS or "http://localhost" in str(self.ALLOWED_ORIGINS):
                errors.append(
                    "⚠️  WARNING: Insecure CORS configuration in production! "
                    f"Current: {self.ALLOWED_ORIGINS}"
                )
            
            if "sqlite" in self.DATABASE_URL:
                errors.append(
                    "⚠️  WARNING: SQLite database in production! "
                    "Use PostgreSQL or MySQL for production deployments."
                )
        
        if errors:
            print("\n" + "="*70)
            print("🔒 SECURITY CONFIGURATION WARNINGS")
            print("="*70)
            for error in errors:
                print(error)
            print("="*70 + "\n")
        
        return len(errors) == 0


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    settings = Settings()
    settings.validate()  # Validate on first load
    return settings


# Global settings instance
settings = get_settings()