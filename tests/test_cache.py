import pytest
from unittest.mock import Mock, MagicMock
from redis import Redis
from redis.exceptions import RedisError

from app.services.cache_service import CacheService


@pytest.fixture
def mock_redis():
    """Create a mock Redis client"""
    redis_mock = Mock(spec=Redis)
    redis_mock.get = MagicMock(return_value=None)
    redis_mock.setex = MagicMock(return_value=True)
    redis_mock.delete = MagicMock(return_value=1)
    redis_mock.keys = MagicMock(return_value=[])
    redis_mock.info = MagicMock(return_value={"keyspace_hits": 100, "keyspace_misses": 50})
    return redis_mock


@pytest.fixture
def cache_service(mock_redis):
    """Create a CacheService with mock Redis"""
    return CacheService(redis_client=mock_redis)


def test_cache_service_disabled_when_no_redis():
    """Test that cache service is disabled when Redis is not provided"""
    cache = CacheService(redis_client=None)
    assert cache.enabled is False
    
    # All operations should return None/False when disabled
    assert cache.get_flag("test") is None
    assert cache.set_flag("test", {}) is False
    assert cache.get_evaluation("test") is None


def test_get_flag_cache_miss(cache_service, mock_redis):
    """Test cache miss when flag doesn't exist in cache"""
    mock_redis.get.return_value = None
    
    result = cache_service.get_flag("test_flag")
    
    assert result is None
    mock_redis.get.assert_called_once_with("flag:data:test_flag")


def test_get_flag_cache_hit(cache_service, mock_redis):
    """Test cache hit when flag exists in cache"""
    import json
    
    flag_data = {
        "id": 1,
        "key": "test_flag",
        "name": "Test Flag",
        "enabled": True,
        "rollout_percentage": 100.0
    }
    
    mock_redis.get.return_value = json.dumps(flag_data)
    
    result = cache_service.get_flag("test_flag")
    
    assert result == flag_data
    mock_redis.get.assert_called_once()


def test_set_flag_success(cache_service, mock_redis):
    """Test successfully setting a flag in cache"""
    import json
    
    flag_data = {
        "id": 1,
        "key": "test_flag",
        "name": "Test Flag"
    }
    
    result = cache_service.set_flag("test_flag", flag_data)
    
    assert result is True
    mock_redis.setex.assert_called_once()
    
    # Verify the call
    call_args = mock_redis.setex.call_args
    assert call_args[0][0] == "flag:data:test_flag"
    assert call_args[0][1] == 300  # default TTL
    assert json.loads(call_args[0][2]) == flag_data


def test_set_flag_custom_ttl(cache_service, mock_redis):
    """Test setting flag with custom TTL"""
    flag_data = {"key": "test"}
    custom_ttl = 600
    
    cache_service.set_flag("test_flag", flag_data, ttl=custom_ttl)
    
    call_args = mock_redis.setex.call_args
    assert call_args[0][1] == custom_ttl


def test_get_evaluation_cache_miss(cache_service, mock_redis):
    """Test evaluation cache miss"""
    mock_redis.get.return_value = None
    
    result = cache_service.get_evaluation("test_flag", user_id="user_123")
    
    assert result is None


def test_get_evaluation_cache_hit(cache_service, mock_redis):
    """Test evaluation cache hit"""
    import json
    
    eval_data = {
        "enabled": True,
        "reason": "Flag enabled for all"
    }
    
    mock_redis.get.return_value = json.dumps(eval_data)
    
    enabled, reason = cache_service.get_evaluation("test_flag", user_id="user_123")
    
    assert enabled is True
    assert reason == "Flag enabled for all"


def test_set_evaluation_without_user(cache_service, mock_redis):
    """Test caching evaluation without user_id"""
    result = cache_service.set_evaluation(
        "test_flag",
        enabled=True,
        reason="Test reason"
    )
    
    assert result is True
    
    # Verify cache key doesn't include user hash
    call_args = mock_redis.setex.call_args
    assert call_args[0][0] == "flag:eval:test_flag"


def test_set_evaluation_with_user(cache_service, mock_redis):
    """Test caching evaluation with user_id"""
    result = cache_service.set_evaluation(
        "test_flag",
        enabled=True,
        reason="Test reason",
        user_id="user_123"
    )
    
    assert result is True
    
    # Verify cache key includes user hash
    call_args = mock_redis.setex.call_args
    cache_key = call_args[0][0]
    assert cache_key.startswith("flag:eval:test_flag:")
    assert len(cache_key.split(":")[-1]) == 16  # 16-char hash


def test_invalidate_flag(cache_service, mock_redis):
    """Test invalidating all cache entries for a flag"""
    # Mock keys method to return some eval keys
    mock_redis.keys.return_value = [
        "flag:eval:test_flag:abc123",
        "flag:eval:test_flag:def456"
    ]
    
    result = cache_service.invalidate_flag("test_flag")
    
    assert result is True
    
    # Should delete data key
    assert mock_redis.delete.call_count == 2
    
    # Should search for eval keys
    mock_redis.keys.assert_called_once_with("flag:eval:test_flag*")


def test_clear_all_cache(cache_service, mock_redis):
    """Test clearing all cache entries"""
    mock_redis.keys.return_value = [
        "flag:data:flag1",
        "flag:data:flag2",
        "flag:eval:flag1:user1"
    ]
    
    result = cache_service.clear_all()
    
    assert result is True
    mock_redis.keys.assert_called_once_with("flag:*")
    mock_redis.delete.assert_called_once()


def test_get_stats_success(cache_service, mock_redis):
    """Test getting cache statistics"""
    mock_redis.keys.return_value = ["flag:data:test1", "flag:data:test2"]
    
    stats = cache_service.get_stats()
    
    assert stats["enabled"] is True
    assert stats["flag_keys"] == 2
    assert stats["keyspace_hits"] == 100
    assert stats["keyspace_misses"] == 50
    assert stats["hit_rate"] == 66.67


def test_get_stats_disabled_cache():
    """Test stats when cache is disabled"""
    cache = CacheService(redis_client=None)
    
    stats = cache.get_stats()
    
    assert stats == {"enabled": False}


def test_redis_error_handling_get(cache_service, mock_redis):
    """Test that Redis errors are handled gracefully on get"""
    mock_redis.get.side_effect = RedisError("Connection failed")
    
    # Should return None instead of raising
    result = cache_service.get_flag("test_flag")
    assert result is None


def test_redis_error_handling_set(cache_service, mock_redis):
    """Test that Redis errors are handled gracefully on set"""
    mock_redis.setex.side_effect = RedisError("Connection failed")
    
    # Should return False instead of raising
    result = cache_service.set_flag("test_flag", {})
    assert result is False


def test_hit_rate_calculation_zero_total():
    """Test hit rate calculation with zero total"""
    rate = CacheService._calculate_hit_rate(0, 0)
    assert rate == 0.0


def test_hit_rate_calculation():
    """Test hit rate calculation"""
    rate = CacheService._calculate_hit_rate(75, 25)
    assert rate == 75.0
    
    rate = CacheService._calculate_hit_rate(50, 50)
    assert rate == 50.0
