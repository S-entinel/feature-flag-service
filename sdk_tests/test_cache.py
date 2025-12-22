"""
Tests for SDK local cache
"""

import pytest
import time
from sdk.cache import LocalCache


def test_cache_basic_get_set():
    """Test basic cache get/set operations"""
    cache = LocalCache(default_ttl=60)
    
    cache.set("test_key", "test_value")
    result = cache.get("test_key")
    
    assert result == "test_value"


def test_cache_miss():
    """Test cache miss returns None"""
    cache = LocalCache(default_ttl=60)
    
    result = cache.get("nonexistent_key")
    
    assert result is None


def test_cache_expiry():
    """Test that cache entries expire after TTL"""
    cache = LocalCache(default_ttl=1)  # 1 second TTL
    
    cache.set("expire_key", "expire_value")
    
    # Should exist immediately
    assert cache.get("expire_key") == "expire_value"
    
    # Wait for expiry
    time.sleep(1.1)
    
    # Should be expired now
    assert cache.get("expire_key") is None


def test_cache_custom_ttl():
    """Test setting custom TTL per entry"""
    cache = LocalCache(default_ttl=60)
    
    cache.set("short_ttl", "value", ttl=1)
    cache.set("long_ttl", "value", ttl=10)
    
    time.sleep(1.1)
    
    assert cache.get("short_ttl") is None
    assert cache.get("long_ttl") == "value"


def test_cache_delete():
    """Test deleting cache entries"""
    cache = LocalCache(default_ttl=60)
    
    cache.set("delete_key", "delete_value")
    assert cache.get("delete_key") == "delete_value"
    
    cache.delete("delete_key")
    assert cache.get("delete_key") is None


def test_cache_delete_nonexistent():
    """Test deleting non-existent key doesn't raise error"""
    cache = LocalCache(default_ttl=60)
    
    # Should not raise
    cache.delete("nonexistent")


def test_cache_clear():
    """Test clearing all cache entries"""
    cache = LocalCache(default_ttl=60)
    
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")
    
    assert cache.size() == 3
    
    cache.clear()
    
    assert cache.size() == 0
    assert cache.get("key1") is None


def test_cache_size():
    """Test getting cache size"""
    cache = LocalCache(default_ttl=60)
    
    assert cache.size() == 0
    
    cache.set("key1", "value1")
    assert cache.size() == 1
    
    cache.set("key2", "value2")
    assert cache.size() == 2
    
    cache.delete("key1")
    assert cache.size() == 1


def test_cache_cleanup_expired():
    """Test manual cleanup of expired entries"""
    cache = LocalCache(default_ttl=1)
    
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")
    
    assert cache.size() == 3
    
    # Wait for expiry
    time.sleep(1.1)
    
    # Size should still be 3 (lazy deletion)
    assert cache.size() == 3
    
    # Cleanup should remove expired entries
    removed = cache.cleanup_expired()
    
    assert removed == 3
    assert cache.size() == 0


def test_cache_thread_safety():
    """Test that cache is thread-safe"""
    import threading
    
    cache = LocalCache(default_ttl=60)
    errors = []
    
    def set_values(start, end):
        try:
            for i in range(start, end):
                cache.set(f"key_{i}", f"value_{i}")
        except Exception as e:
            errors.append(e)
    
    # Create multiple threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=set_values, args=(i*100, (i+1)*100))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads
    for thread in threads:
        thread.join()
    
    # Should have no errors
    assert len(errors) == 0
    
    # Should have 500 entries
    assert cache.size() == 500


def test_cache_different_types():
    """Test caching different data types"""
    cache = LocalCache(default_ttl=60)
    
    # String
    cache.set("string", "test")
    assert cache.get("string") == "test"
    
    # Integer
    cache.set("int", 42)
    assert cache.get("int") == 42
    
    # List
    cache.set("list", [1, 2, 3])
    assert cache.get("list") == [1, 2, 3]
    
    # Dict
    cache.set("dict", {"key": "value"})
    assert cache.get("dict") == {"key": "value"}
    
    # Object
    class TestObj:
        def __init__(self, val):
            self.val = val
    
    obj = TestObj(100)
    cache.set("object", obj)
    cached_obj = cache.get("object")
    assert cached_obj.val == 100


def test_cache_overwrite():
    """Test overwriting existing cache entries"""
    cache = LocalCache(default_ttl=60)
    
    cache.set("key", "value1")
    assert cache.get("key") == "value1"
    
    cache.set("key", "value2")
    assert cache.get("key") == "value2"