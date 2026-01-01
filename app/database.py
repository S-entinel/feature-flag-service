from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.flag import Base
from app.services.cache_service import CacheService
from app.config import settings

# Database engine using centralized config
engine = create_engine(
    settings.DATABASE_URL, 
    connect_args=settings.sqlalchemy_connect_args,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=300,  # Recycle connections after 5 minutes (good for serverless)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Cache service (disabled for Vercel serverless)
_cache_service = None


def get_cache_service() -> CacheService:
    """
    Get cache service (disabled for Vercel serverless deployment)
    
    Vercel serverless functions are stateless, so Redis caching
    doesn't provide much benefit. We disable it for simplicity.
    """
    global _cache_service
    
    if _cache_service is None:
        # Create disabled cache service (redis_client=None)
        _cache_service = CacheService(redis_client=None)
        print("ℹ️  Cache service disabled (Vercel serverless deployment)")
    
    return _cache_service


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print(f"✅ Database initialized: {settings.DATABASE_URL[:50]}...")


def get_db():
    """Dependency for getting DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()