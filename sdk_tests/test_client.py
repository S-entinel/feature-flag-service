"""
Tests for SDK client
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import httpx

from sdk.client import FeatureFlagClient
from sdk.exceptions import (
    FlagNotFoundError,
    APIError,
    NetworkError,
    TimeoutError as SDKTimeoutError
)
from sdk.models import Flag, EvaluationResult


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx client"""
    with patch('sdk.client.httpx.Client') as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def client(mock_httpx_client):
    """Create a FeatureFlagClient with mocked HTTP"""
    return FeatureFlagClient("http://localhost:8000")


def test_client_initialization():
    """Test client initialization"""
    client = FeatureFlagClient(
        "http://localhost:8000",
        timeout=10.0,
        enable_cache=True,
        cache_ttl=120
    )
    
    assert client.base_url == "http://localhost:8000"
    assert client.timeout == 10.0
    assert client.cache_enabled is True
    assert client.cache is not None


def test_client_initialization_no_cache():
    """Test client initialization without cache"""
    client = FeatureFlagClient(
        "http://localhost:8000",
        enable_cache=False
    )
    
    assert client.cache_enabled is False
    assert client.cache is None


def test_context_manager(mock_httpx_client):
    """Test client as context manager"""
    with FeatureFlagClient("http://localhost:8000") as client:
        assert client is not None
    
    # Should have closed the HTTP client
    mock_httpx_client.close.assert_called_once()


def test_is_enabled_true(client, mock_httpx_client):
    """Test is_enabled returns True when flag is enabled"""
    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "key": "test_flag",
        "enabled": True,
        "reason": "Flag enabled for all users"
    }
    mock_httpx_client.request.return_value = mock_response
    
    result = client.is_enabled("test_flag", user_id="user_123")
    
    assert result is True


def test_is_enabled_false(client, mock_httpx_client):
    """Test is_enabled returns False when flag is disabled"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "key": "test_flag",
        "enabled": False,
        "reason": "Flag is disabled"
    }
    mock_httpx_client.request.return_value = mock_response
    
    result = client.is_enabled("test_flag")
    
    assert result is False


def test_evaluate_success(client, mock_httpx_client):
    """Test successful flag evaluation"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "key": "test_flag",
        "enabled": True,
        "reason": "Flag enabled for all users"
    }
    mock_httpx_client.request.return_value = mock_response
    
    result = client.evaluate("test_flag", user_id="user_123")
    
    assert isinstance(result, EvaluationResult)
    assert result.key == "test_flag"
    assert result.enabled is True
    assert result.reason == "Flag enabled for all users"


def test_evaluate_flag_not_found(client, mock_httpx_client):
    """Test evaluate raises FlagNotFoundError for non-existent flag"""
    mock_response = Mock()
    mock_response.status_code = 404
    mock_httpx_client.request.return_value = mock_response
    
    with pytest.raises(FlagNotFoundError) as exc_info:
        client.evaluate("nonexistent_flag")
    
    assert exc_info.value.flag_key == "nonexistent_flag"


def test_evaluate_uses_cache(client, mock_httpx_client):
    """Test that evaluate uses cache on second call"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "key": "cached_flag",
        "enabled": True,
        "reason": "Cached"
    }
    mock_httpx_client.request.return_value = mock_response
    
    # First call - cache miss
    result1 = client.evaluate("cached_flag", user_id="user_123")
    assert result1.enabled is True
    
    # Second call - should use cache (no new request)
    call_count_before = mock_httpx_client.request.call_count
    result2 = client.evaluate("cached_flag", user_id="user_123")
    call_count_after = mock_httpx_client.request.call_count
    
    assert result2.enabled is True
    assert call_count_before == call_count_after  # No new request


def test_evaluate_all(client, mock_httpx_client):
    """Test evaluating multiple flags"""
    def mock_request_side_effect(method, url, **kwargs):
        mock_response = Mock()
        mock_response.status_code = 200
        
        if "flag_a" in url:
            mock_response.json.return_value = {
                "key": "flag_a",
                "enabled": True,
                "reason": "Enabled"
            }
        elif "flag_b" in url:
            mock_response.json.return_value = {
                "key": "flag_b",
                "enabled": False,
                "reason": "Disabled"
            }
        elif "flag_c" in url:
            mock_response.status_code = 404
        
        return mock_response
    
    mock_httpx_client.request.side_effect = mock_request_side_effect
    
    results = client.evaluate_all(["flag_a", "flag_b", "flag_c"], user_id="user_123")
    
    # Should have 2 results (flag_c not found)
    assert len(results) == 2
    assert results["flag_a"].enabled is True
    assert results["flag_b"].enabled is False


def test_get_flag_success(client, mock_httpx_client):
    """Test getting flag details"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": 1,
        "key": "test_flag",
        "name": "Test Flag",
        "description": "A test flag",
        "enabled": True,
        "rollout_percentage": 100.0,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    }
    mock_httpx_client.request.return_value = mock_response
    
    flag = client.get_flag("test_flag")
    
    assert isinstance(flag, Flag)
    assert flag.key == "test_flag"
    assert flag.name == "Test Flag"
    assert flag.enabled is True


def test_get_flag_not_found(client, mock_httpx_client):
    """Test getting non-existent flag"""
    mock_response = Mock()
    mock_response.status_code = 404
    mock_httpx_client.request.return_value = mock_response
    
    with pytest.raises(FlagNotFoundError):
        client.get_flag("nonexistent")


def test_list_flags(client, mock_httpx_client):
    """Test listing all flags"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "id": 1,
            "key": "flag_1",
            "name": "Flag 1",
            "description": None,
            "enabled": True,
            "rollout_percentage": 100.0,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        },
        {
            "id": 2,
            "key": "flag_2",
            "name": "Flag 2",
            "description": None,
            "enabled": False,
            "rollout_percentage": 50.0,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
    ]
    mock_httpx_client.request.return_value = mock_response
    
    flags = client.list_flags()
    
    assert len(flags) == 2
    assert flags[0].key == "flag_1"
    assert flags[1].key == "flag_2"


def test_create_flag(client, mock_httpx_client):
    """Test creating a new flag"""
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {
        "id": 1,
        "key": "new_flag",
        "name": "New Flag",
        "description": "A new flag",
        "enabled": False,
        "rollout_percentage": 100.0,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    }
    mock_httpx_client.request.return_value = mock_response
    
    flag = client.create_flag(
        key="new_flag",
        name="New Flag",
        description="A new flag",
        enabled=False,
        rollout_percentage=100.0
    )
    
    assert flag.key == "new_flag"
    assert flag.name == "New Flag"


def test_update_flag(client, mock_httpx_client):
    """Test updating a flag"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": 1,
        "key": "test_flag",
        "name": "Updated Name",
        "description": None,
        "enabled": True,
        "rollout_percentage": 75.0,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    }
    mock_httpx_client.request.return_value = mock_response
    
    flag = client.update_flag(
        "test_flag",
        name="Updated Name",
        enabled=True,
        rollout_percentage=75.0
    )
    
    assert flag.name == "Updated Name"
    assert flag.enabled is True
    assert flag.rollout_percentage == 75.0


def test_update_flag_not_found(client, mock_httpx_client):
    """Test updating non-existent flag"""
    mock_response = Mock()
    mock_response.status_code = 404
    mock_httpx_client.request.return_value = mock_response
    
    with pytest.raises(FlagNotFoundError):
        client.update_flag("nonexistent", enabled=True)


def test_delete_flag(client, mock_httpx_client):
    """Test deleting a flag"""
    mock_response = Mock()
    mock_response.status_code = 204
    mock_httpx_client.request.return_value = mock_response
    
    result = client.delete_flag("test_flag")
    
    assert result is True


def test_delete_flag_not_found(client, mock_httpx_client):
    """Test deleting non-existent flag"""
    mock_response = Mock()
    mock_response.status_code = 404
    mock_httpx_client.request.return_value = mock_response
    
    with pytest.raises(FlagNotFoundError):
        client.delete_flag("nonexistent")


def test_network_error(client, mock_httpx_client):
    """Test handling of network errors"""
    mock_httpx_client.request.side_effect = httpx.NetworkError("Connection failed")
    
    with pytest.raises(NetworkError):
        client.evaluate("test_flag")


def test_timeout_error(client, mock_httpx_client):
    """Test handling of timeout errors"""
    mock_httpx_client.request.side_effect = httpx.TimeoutException("Timeout")
    
    with pytest.raises(SDKTimeoutError):
        client.evaluate("test_flag")


def test_api_error_500(client, mock_httpx_client):
    """Test handling of 500 API errors"""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.json.return_value = {"detail": "Internal server error"}
    mock_httpx_client.request.return_value = mock_response
    
    with pytest.raises(APIError) as exc_info:
        client.evaluate("test_flag")
    
    assert exc_info.value.status_code == 500


def test_retry_on_network_error(client, mock_httpx_client):
    """Test that requests are retried on network errors"""
    # First two calls fail, third succeeds
    call_count = [0]
    
    def side_effect(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] <= 2:
            raise httpx.NetworkError("Connection failed")
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "key": "test_flag",
            "enabled": True,
            "reason": "Success after retry"
        }
        return mock_response
    
    mock_httpx_client.request.side_effect = side_effect
    
    result = client.evaluate("test_flag")
    
    assert result.enabled is True
    assert call_count[0] == 3  # Should have retried twice


def test_clear_cache(client):
    """Test clearing cache"""
    # Add something to cache
    client.cache.set("test", "value")
    assert client.cache.size() == 1
    
    client.clear_cache()
    
    assert client.cache.size() == 0


def test_get_cache_stats(client):
    """Test getting cache statistics"""
    client.cache.set("key1", "value1")
    client.cache.set("key2", "value2")
    
    stats = client.get_cache_stats()
    
    assert stats["enabled"] is True
    assert stats["size"] == 2


def test_get_cache_stats_disabled():
    """Test cache stats when cache is disabled"""
    client = FeatureFlagClient("http://localhost:8000", enable_cache=False)
    
    stats = client.get_cache_stats()
    
    assert stats["enabled"] is False
    assert stats["size"] == 0


def test_base_url_trailing_slash():
    """Test that trailing slash is removed from base URL"""
    client = FeatureFlagClient("http://localhost:8000/")
    
    assert client.base_url == "http://localhost:8000"