"""
Local in-memory cache for the SDK to reduce API calls
"""

import time
from typing import Optional, Dict, Any, Tuple
from threading import Lock


class LocalCache:
    """
    Simple thread-safe in-memory cache with TTL
    
    This provides client-side caching to reduce API calls
    even further beyond the server's Redis cache.
    """
    
    def __init__(self, default_ttl: int = 60):
        """
        Initialize local cache
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 60s)
        """
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._lock = Lock()
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if not expired
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            value, expiry = self._cache[key]
            
            # Check if expired
            if time.time() > expiry:
                del self._cache[key]
                return None
            
            return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache with TTL
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        with self._lock:
            ttl = ttl or self.default_ttl
            expiry = time.time() + ttl
            self._cache[key] = (value, expiry)
    
    def delete(self, key: str) -> None:
        """
        Delete a key from cache
        
        Args:
            key: Cache key to delete
        """
        with self._lock:
            self._cache.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cached values"""
        with self._lock:
            self._cache.clear()
    
    def size(self) -> int:
        """Get number of items in cache"""
        with self._lock:
            return len(self._cache)
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries
        
        Returns:
            Number of expired entries removed
        """
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, (_, expiry) in self._cache.items()
                if current_time > expiry
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)