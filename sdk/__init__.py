"""
Feature Flag SDK - Python Client Library

A simple, fast client for the Feature Flag Service with built-in caching.

Example usage:
    from feature_flags import FeatureFlagClient
    
    client = FeatureFlagClient("http://localhost:8000")
    
    if client.is_enabled("new_feature", user_id="user_123"):
        # Show new feature
        pass
"""

from sdk.client import FeatureFlagClient
from sdk.exceptions import (
    FeatureFlagError,
    FlagNotFoundError,
    APIError,
    ValidationError
)
from sdk.models import Flag, EvaluationResult

__version__ = "1.0.0"
__all__ = [
    "FeatureFlagClient",
    "FeatureFlagError",
    "FlagNotFoundError", 
    "APIError",
    "ValidationError",
    "Flag",
    "EvaluationResult"
]