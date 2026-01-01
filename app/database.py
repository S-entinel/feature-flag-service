from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from redis import Redis
from redis.exceptions import RedisError
from app.models.flag import Base
from app.services.cache_service import CacheService
from app.config import settings

# Database engine using centralized config
engine = create_engine(
    settings.DATABASE_URL, 
    connect_args=settings.sqlalchemy_connect_args
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
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # Test connection
            _redis_client.ping()
            print(f"✅ Redis connected: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except (RedisError, ConnectionError) as e:
            print(f"⚠️  Redis connection failed: {e}")
            print("⚠️  Running without cache")
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
            print("ℹ️  Cache service disabled (Redis not available)")
    
    return _cache_service


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print(f"✅ Database initialized: {settings.DATABASE_URL}")


def get_db():
    """Dependency for getting DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()