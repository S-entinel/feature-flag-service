"""
Vercel serverless entry point for Feature Flag Service
"""

from mangum import Mangum
from app.main import app

# Mangum adapter converts FastAPI to ASGI handler for Vercel
handler = Mangum(app, lifespan="off")