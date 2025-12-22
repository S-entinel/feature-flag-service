"""
Feature Flag SDK Client

Main client for interacting with the Feature Flag Service
"""

import httpx
from typing import Optional, List, Dict
from urllib.parse import urljoin

from sdk.exceptions import (
    FlagNotFoundError,
    APIError,
    NetworkError,
    TimeoutError as SDKTimeoutError
)
from sdk.models import Flag, EvaluationResult
from sdk.cache import LocalCache


class FeatureFlagClient:
    """
    Client for the Feature Flag Service
    
    Provides methods to evaluate flags, manage flags, and handle caching.
    
    Example:
        client = FeatureFlagClient("http://localhost:8000")
        
        # Check if flag is enabled
        if client.is_enabled("new_feature", user_id="user_123"):
            # Show new feature
            pass
        
        # Get detailed evaluation
        result = client.evaluate("new_feature", user_id="user_123")
        print(f"Enabled: {result.enabled}, Reason: {result.reason}")
    """
    
    def __init__(
        self,
        base_url: str,
        timeout: float = 5.0,
        enable_cache: bool = True,
        cache_ttl: int = 60,
        max_retries: int = 2
    ):
        """
        Initialize Feature Flag Client
        
        Args:
            base_url: Base URL of the feature flag service (e.g., "http://localhost:8000")
            timeout: Request timeout in seconds (default: 5.0)
            enable_cache: Enable local caching (default: True)
            cache_ttl: Cache TTL in seconds (default: 60)
            max_retries: Maximum number of retries for failed requests (default: 2)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        
        # HTTP client with timeout
        self.client = httpx.Client(
            timeout=timeout,
            follow_redirects=True
        )
        
        # Local cache
        self.cache_enabled = enable_cache
        self.cache = LocalCache(default_ttl=cache_ttl) if enable_cache else None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close HTTP client"""
        self.close()
    
    def close(self):
        """Close the HTTP client"""
        self.client.close()
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        """
        Make HTTP request with error handling and retries
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., "/flags/my_flag")
            **kwargs: Additional arguments to pass to httpx
            
        Returns:
            HTTP response
            
        Raises:
            NetworkError: If request fails
            TimeoutError: If request times out
            APIError: If API returns error response
        """
        url = urljoin(self.base_url, endpoint)
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.request(method, url, **kwargs)
                
                # Check for HTTP errors
                if response.status_code >= 400:
                    if response.status_code == 404:
                        # Let caller handle 404 specifically
                        return response
                    
                    try:
                        error_data = response.json()
                        message = error_data.get("detail", "Unknown error")
                    except Exception:
                        message = response.text or "Unknown error"
                    
                    raise APIError(response.status_code, message)
                
                return response
                
            except httpx.TimeoutException as e:
                if attempt == self.max_retries:
                    raise SDKTimeoutError(f"Request timed out after {self.timeout}s") from e
                continue
                
            except httpx.NetworkError as e:
                if attempt == self.max_retries:
                    raise NetworkError(f"Network error: {str(e)}") from e
                continue
            
            except httpx.HTTPError as e:
                if attempt == self.max_retries:
                    raise NetworkError(f"HTTP error: {str(e)}") from e
                continue
        
        # Should never reach here
        raise NetworkError("Max retries exceeded")
    
    def is_enabled(self, flag_key: str, user_id: Optional[str] = None) -> bool:
        """
        Simple check if a flag is enabled
        
        This is the most common operation - just returns True/False.
        Uses caching for fast lookups.
        
        Args:
            flag_key: The flag key to check
            user_id: Optional user ID for percentage rollout
            
        Returns:
            True if flag is enabled, False otherwise
            
        Example:
            if client.is_enabled("new_checkout", user_id="user_123"):
                show_new_checkout()
        """
        result = self.evaluate(flag_key, user_id)
        return result.enabled
    
    def evaluate(
        self,
        flag_key: str,
        user_id: Optional[str] = None
    ) -> EvaluationResult:
        """
        Evaluate a flag and get detailed result
        
        Returns both the enabled status and the reason.
        Uses caching for performance.
        
        Args:
            flag_key: The flag key to evaluate
            user_id: Optional user ID for percentage rollout
            
        Returns:
            EvaluationResult with enabled status and reason
            
        Raises:
            FlagNotFoundError: If flag doesn't exist
            APIError: If API returns an error
            NetworkError: If network request fails
            
        Example:
            result = client.evaluate("new_feature", user_id="user_123")
            print(f"Enabled: {result.enabled}")
            print(f"Reason: {result.reason}")
        """
        # Check cache first
        cache_key = f"eval:{flag_key}:{user_id or 'none'}"
        if self.cache_enabled and self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached
        
        # Make API request
        endpoint = f"/flags/{flag_key}/evaluate"
        params = {"user_id": user_id} if user_id else {}
        
        response = self._make_request("GET", endpoint, params=params)
        
        if response.status_code == 404:
            raise FlagNotFoundError(flag_key)
        
        data = response.json()
        result = EvaluationResult.from_dict(data)
        
        # Cache the result
        if self.cache_enabled and self.cache:
            self.cache.set(cache_key, result)
        
        return result
    
    def evaluate_all(
        self,
        flag_keys: List[str],
        user_id: Optional[str] = None
    ) -> Dict[str, EvaluationResult]:
        """
        Evaluate multiple flags at once
        
        More efficient than calling evaluate() multiple times.
        
        Args:
            flag_keys: List of flag keys to evaluate
            user_id: Optional user ID for percentage rollout
            
        Returns:
            Dictionary mapping flag keys to evaluation results
            
        Example:
            results = client.evaluate_all(
                ["feature_a", "feature_b", "feature_c"],
                user_id="user_123"
            )
            
            if results["feature_a"].enabled:
                show_feature_a()
        """
        results = {}
        
        for flag_key in flag_keys:
            try:
                results[flag_key] = self.evaluate(flag_key, user_id)
            except FlagNotFoundError:
                # Skip flags that don't exist
                continue
        
        return results
    
    def get_flag(self, flag_key: str) -> Flag:
        """
        Get full flag details
        
        Args:
            flag_key: The flag key
            
        Returns:
            Flag object with all details
            
        Raises:
            FlagNotFoundError: If flag doesn't exist
        """
        # Check cache
        cache_key = f"flag:{flag_key}"
        if self.cache_enabled and self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return cached
        
        # Make API request
        endpoint = f"/flags/{flag_key}"
        response = self._make_request("GET", endpoint)
        
        if response.status_code == 404:
            raise FlagNotFoundError(flag_key)
        
        data = response.json()
        flag = Flag.from_dict(data)
        
        # Cache the flag
        if self.cache_enabled and self.cache:
            self.cache.set(cache_key, flag)
        
        return flag
    
    def list_flags(self, skip: int = 0, limit: int = 100) -> List[Flag]:
        """
        List all flags
        
        Args:
            skip: Number of flags to skip (pagination)
            limit: Maximum number of flags to return
            
        Returns:
            List of Flag objects
        """
        endpoint = "/flags/"
        params = {"skip": skip, "limit": limit}
        
        response = self._make_request("GET", endpoint, params=params)
        data = response.json()
        
        return [Flag.from_dict(flag_data) for flag_data in data]
    
    def create_flag(
        self,
        key: str,
        name: str,
        description: Optional[str] = None,
        enabled: bool = False,
        rollout_percentage: float = 100.0
    ) -> Flag:
        """
        Create a new flag
        
        Args:
            key: Unique flag key
            name: Human-readable name
            description: Optional description
            enabled: Initial enabled state
            rollout_percentage: Rollout percentage (0-100)
            
        Returns:
            Created Flag object
            
        Raises:
            APIError: If flag already exists or validation fails
        """
        endpoint = "/flags/"
        payload = {
            "key": key,
            "name": name,
            "description": description,
            "enabled": enabled,
            "rollout_percentage": rollout_percentage
        }
        
        response = self._make_request("POST", endpoint, json=payload)
        data = response.json()
        
        return Flag.from_dict(data)
    
    def update_flag(
        self,
        flag_key: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        enabled: Optional[bool] = None,
        rollout_percentage: Optional[float] = None
    ) -> Flag:
        """
        Update an existing flag
        
        Args:
            flag_key: The flag key to update
            name: New name (optional)
            description: New description (optional)
            enabled: New enabled state (optional)
            rollout_percentage: New rollout percentage (optional)
            
        Returns:
            Updated Flag object
            
        Raises:
            FlagNotFoundError: If flag doesn't exist
        """
        endpoint = f"/flags/{flag_key}"
        payload = {}
        
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if enabled is not None:
            payload["enabled"] = enabled
        if rollout_percentage is not None:
            payload["rollout_percentage"] = rollout_percentage
        
        response = self._make_request("PUT", endpoint, json=payload)
        
        if response.status_code == 404:
            raise FlagNotFoundError(flag_key)
        
        data = response.json()
        
        # Invalidate cache for this flag
        if self.cache_enabled and self.cache:
            self.cache.delete(f"flag:{flag_key}")
            # Also clear evaluation cache (could have many user-specific entries)
            # Note: This is a simple approach; in production you might want more granular control
        
        return Flag.from_dict(data)
    
    def delete_flag(self, flag_key: str) -> bool:
        """
        Delete a flag
        
        Args:
            flag_key: The flag key to delete
            
        Returns:
            True if deleted successfully
            
        Raises:
            FlagNotFoundError: If flag doesn't exist
        """
        endpoint = f"/flags/{flag_key}"
        response = self._make_request("DELETE", endpoint)
        
        if response.status_code == 404:
            raise FlagNotFoundError(flag_key)
        
        # Invalidate cache
        if self.cache_enabled and self.cache:
            self.cache.delete(f"flag:{flag_key}")
        
        return True
    
    def clear_cache(self):
        """Clear all cached data"""
        if self.cache_enabled and self.cache:
            self.cache.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats (size, cleanup info, etc.)
        """
        if not self.cache_enabled or not self.cache:
            return {"enabled": False, "size": 0}
        
        expired = self.cache.cleanup_expired()
        
        return {
            "enabled": True,
            "size": self.cache.size(),
            "expired_cleaned": expired
        }