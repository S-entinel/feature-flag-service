from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.api import flags

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(
    title="Feature Flag Service",
    description="A simple feature flag service for controlling feature rollouts",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(flags.router)


@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "message": "Feature Flag Service is running",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check for monitoring"""
    return {"status": "healthy"}