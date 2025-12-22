import json
import hashlib
from typing import Optional, Any
from redis import Redis
from redis.exceptions import RedisError


class CacheService:
    """Redis cache service for feature flags"""
    
    def __init__(self, redis_client: Optional[Redis] = None):
        """
        Initialize cache service
        
        Args:
            redis_client: Optional Redis client. If None, caching is disabled.
        """
        self.redis = redis_client
        self.default_ttl = 300  # 5 minutes
        self.enabled = redis_client is not None
    
    def _make_key(self, prefix: str, identifier: str) -> str:
        """Create a cache key with prefix"""
        return f"flag:{prefix}:{identifier}"
    
    def get_flag(self, flag_key: str) -> Optional[dict]:
        """
        Get flag from cache
        
        Args:
            flag_key: The flag key to retrieve
            
        Returns:
            Flag data as dict, or None if not in cache
        """
        if not self.enabled:
            return None
        
        try:
            cache_key = self._make_key("data", flag_key)
            data = self.redis.get(cache_key)
            
            if data:
                return json.loads(data)
            return None
        except (RedisError, json.JSONDecodeError):
            # If cache fails, return None and let caller fetch from DB
            return None
    
    def set_flag(self, flag_key: str, flag_data: dict, ttl: Optional[int] = None) -> bool:
        """
        Store flag in cache
        
        Args:
            flag_key: The flag key
            flag_data: Flag data to cache
            ttl: Time to live in seconds (uses default if None)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            cache_key = self._make_key("data", flag_key)
            ttl = ttl or self.default_ttl
            
            self.redis.setex(
                cache_key,
                ttl,
                json.dumps(flag_data)
            )
            return True
        except (RedisError, TypeError):
            return False
    
    def get_evaluation(self, flag_key: str, user_id: Optional[str] = None) -> Optional[tuple[bool, str]]:
        """
        Get cached evaluation result
        
        Args:
            flag_key: The flag key
            user_id: Optional user ID for user-specific evaluation
            
        Returns:
            Tuple of (enabled, reason) or None if not cached
        """
        if not self.enabled:
            return None
        
        try:
            # Create cache key based on flag and user
            if user_id:
                # Hash user_id to keep cache keys reasonable length
                user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:16]
                cache_key = self._make_key("eval", f"{flag_key}:{user_hash}")
            else:
                cache_key = self._make_key("eval", flag_key)
            
            data = self.redis.get(cache_key)
            
            if data:
                result = json.loads(data)
                return result["enabled"], result["reason"]
            return None
        except (RedisError, json.JSONDecodeError, KeyError):
            return None
    
    def set_evaluation(
        self, 
        flag_key: str, 
        enabled: bool, 
        reason: str,
        user_id: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache evaluation result
        
        Args:
            flag_key: The flag key
            enabled: Whether flag is enabled
            reason: Reason for the evaluation result
            user_id: Optional user ID for user-specific evaluation
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            if user_id:
                user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:16]
                cache_key = self._make_key("eval", f"{flag_key}:{user_hash}")
            else:
                cache_key = self._make_key("eval", flag_key)
            
            ttl = ttl or self.default_ttl
            
            data = {
                "enabled": enabled,
                "reason": reason
            }
            
            self.redis.setex(
                cache_key,
                ttl,
                json.dumps(data)
            )
            return True
        except (RedisError, TypeError):
            return False
    
    def invalidate_flag(self, flag_key: str) -> bool:
        """
        Invalidate all cache entries for a flag
        
        Args:
            flag_key: The flag key to invalidate
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            # Delete flag data
            data_key = self._make_key("data", flag_key)
            self.redis.delete(data_key)
            
            # Delete all evaluation caches for this flag
            # Use pattern matching to find all eval keys
            pattern = self._make_key("eval", f"{flag_key}*")
            keys = self.redis.keys(pattern)
            
            if keys:
                self.redis.delete(*keys)
            
            return True
        except RedisError:
            return False
    
    def clear_all(self) -> bool:
        """
        Clear all flag caches (use with caution!)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            pattern = "flag:*"
            keys = self.redis.keys(pattern)
            
            if keys:
                self.redis.delete(*keys)
            
            return True
        except RedisError:
            return False
    
    def get_stats(self) -> dict:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        if not self.enabled:
            return {"enabled": False}
        
        try:
            info = self.redis.info("stats")
            
            # Count our keys
            flag_keys = len(self.redis.keys("flag:*"))
            
            return {
                "enabled": True,
                "flag_keys": flag_keys,
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }
        except RedisError:
            return {"enabled": True, "error": "Could not fetch stats"}
    
    @staticmethod
    def _calculate_hit_rate(hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)
