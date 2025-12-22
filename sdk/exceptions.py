"""
Custom exceptions for the Feature Flag SDK
"""


class FeatureFlagError(Exception):
    """Base exception for all SDK errors"""
    pass


class FlagNotFoundError(FeatureFlagError):
    """Raised when a flag doesn't exist"""
    def __init__(self, flag_key: str):
        self.flag_key = flag_key
        super().__init__(f"Flag '{flag_key}' not found")


class APIError(FeatureFlagError):
    """Raised when the API returns an error"""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error {status_code}: {message}")


class ValidationError(FeatureFlagError):
    """Raised when validation fails"""
    pass


class NetworkError(FeatureFlagError):
    """Raised when network request fails"""
    pass


class TimeoutError(FeatureFlagError):
    """Raised when request times out"""
    pass