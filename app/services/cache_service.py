"""
Cache service for feature flags using Redis (optional)
"""

import json
import hashlib
from typing import Optional, Tuple, Any

# Try to import Redis, but make it optional
try:
    from redis import Redis, RedisError
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    Redis = Any
    RedisError = Exception


class CacheService:
    """Service for caching feature flags and evaluations in Redis"""
    
    def __init__(self, redis_client: Optional[Any] = None, ttl: int = 300):
        """
        Initialize cache service
        
        Args:
            redis_client: Redis client instance (None = caching disabled)
            ttl: Time-to-live for cache entries in seconds
        """
        self.redis = redis_client
        self.ttl = ttl
        self.enabled = redis_client is not None
    
    def _get_flag_key(self, flag_key: str) -> str:
        """Get Redis key for flag data"""
        return f"flag:data:{flag_key}"
    
    def _get_eval_key(self, flag_key: str, user_id: Optional[str] = None) -> str:
        """Get Redis key for flag evaluation"""
        if user_id:
            user_hash = hashlib.md5(user_id.encode()).hexdigest()[:16]
            return f"flag:eval:{flag_key}:{user_hash}"
        return f"flag:eval:{flag_key}"
    
    def get_flag(self, flag_key: str) -> Optional[dict]:
        """Get cached flag data"""
        if not self.enabled:
            return None
        
        try:
            key = self._get_flag_key(flag_key)
            data = self.redis.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            print(f"Cache get error: {e}")
        
        return None
    
    def set_flag(self, flag_key: str, flag_data: dict) -> bool:
        """Cache flag data"""
        if not self.enabled:
            return False
        
        try:
            key = self._get_flag_key(flag_key)
            data = json.dumps(flag_data)
            self.redis.setex(key, self.ttl, data)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def get_evaluation(self, flag_key: str, user_id: Optional[str] = None) -> Optional[Tuple[bool, str]]:
        """Get cached evaluation result"""
        if not self.enabled:
            return None
        
        try:
            key = self._get_eval_key(flag_key, user_id)
            data = self.redis.get(key)
            if data:
                result = json.loads(data)
                return (result['enabled'], result['reason'])
        except Exception as e:
            print(f"Cache get error: {e}")
        
        return None
    
    def set_evaluation(
        self, 
        flag_key: str, 
        enabled: bool, 
        reason: str,
        user_id: Optional[str] = None
    ) -> bool:
        """Cache evaluation result"""
        if not self.enabled:
            return False
        
        try:
            key = self._get_eval_key(flag_key, user_id)
            data = json.dumps({'enabled': enabled, 'reason': reason})
            self.redis.setex(key, self.ttl, data)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def invalidate_flag(self, flag_key: str) -> bool:
        """Invalidate all cache entries for a flag"""
        if not self.enabled:
            return False
        
        try:
            data_key = self._get_flag_key(flag_key)
            self.redis.delete(data_key)
            
            eval_pattern = f"flag:eval:{flag_key}*"
            eval_keys = self.redis.keys(eval_pattern)
            if eval_keys:
                self.redis.delete(*eval_keys)
            
            return True
        except Exception as e:
            print(f"Cache invalidate error: {e}")
            return False
    
    def clear_all(self) -> bool:
        """Clear all cache entries"""
        if not self.enabled:
            return False
        
        try:
            keys = self.redis.keys("flag:*")
            if keys:
                self.redis.delete(*keys)
            return True
        except Exception as e:
            print(f"Cache clear error: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self.enabled:
            return {
                "enabled": False,
                "message": "Cache is disabled"
            }
        
        try:
            info = self.redis.info()
            return {
                "enabled": True,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "keys": len(self.redis.keys("flag:*"))
            }
        except Exception as e:
            return {
                "enabled": True,
                "error": str(e)
            }