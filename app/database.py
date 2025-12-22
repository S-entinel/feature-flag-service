import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from redis import Redis
from redis.exceptions import RedisError
from app.models.flag import Base
from app.services.cache_service import CacheService

# SQLite for development (change to PostgreSQL for production)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./feature_flags.db")

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Redis client (singleton)
_redis_client = None
_cache_service = None


def get_redis_client() -> Redis:
    """Get or create Redis client"""
    global _redis_client
    
    if _redis_client is None:
        try:
            _redis_client = Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # Test connection
            _redis_client.ping()
            print(f"✅ Redis connected: {REDIS_HOST}:{REDIS_PORT}")
        except (RedisError, ConnectionError) as e:
            print(f"⚠️ Redis connection failed: {e}")
            print("⚠️ Running without cache")
            _redis_client = None
    
    return _redis_client


def get_cache_service() -> CacheService:
    """Get or create cache service"""
    global _cache_service
    
    if _cache_service is None:
        redis_client = get_redis_client()
        _cache_service = CacheService(redis_client)
        
        if _cache_service.enabled:
            print("✅ Cache service enabled")
        else:
            print("ℹ️ Cache service disabled (Redis not available)")
    
    return _cache_service


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for getting DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
