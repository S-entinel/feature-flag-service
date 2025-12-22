from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.flag import Base

# SQLite for development (change to PostgreSQL for production)
DATABASE_URL = "sqlite:///./feature_flags.db"

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Only for SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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