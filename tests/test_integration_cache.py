import pytest
from unittest.mock import Mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.flag import Base, Flag
from app.services.cache_service import CacheService
from app.services.flag_service import FlagService
from app.schemas import FlagCreate, FlagUpdate


# Test database
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_cache():
    """Create a mock cache service"""
    cache = Mock(spec=CacheService)
    cache.enabled = True
    cache.get_flag = Mock(return_value=None)
    cache.set_flag = Mock(return_value=True)
    cache.get_evaluation = Mock(return_value=None)
    cache.set_evaluation = Mock(return_value=True)
    cache.invalidate_flag = Mock(return_value=True)
    return cache


@pytest.fixture
def flag_service(mock_cache):
    """Create flag service with mock cache"""
    return FlagService(cache=mock_cache)


@pytest.fixture
def flag_service_no_cache():
    """Create flag service without cache"""
    return FlagService(cache=None)


def test_create_flag_with_cache(db_session, flag_service, mock_cache):
    """Test creating a flag caches it"""
    flag_data = FlagCreate(
        key="test_flag",
        name="Test Flag",
        enabled=True,
        rollout_percentage=100.0
    )
    
    flag = flag_service.create_flag(db_session, flag_data)
    
    assert flag.key == "test_flag"
    assert mock_cache.set_flag.called


def test_get_flag_uses_cache(db_session, flag_service, mock_cache):
    """Test that get_flag checks cache first"""
    # Create a flag in DB
    flag_data = FlagCreate(
        key="cached_flag",
        name="Cached Flag",
        enabled=True,
        rollout_percentage=100.0
    )
    flag_service.create_flag(db_session, flag_data)
    
    # Mock cache to return flag
    import json
    cached_flag = {
        "id": 1,
        "key": "cached_flag",
        "name": "Cached Flag",
        "description": None,
        "enabled": True,
        "rollout_percentage": 100.0,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    }
    mock_cache.get_flag.return_value = cached_flag
    
    # Get flag - should use cache
    flag = flag_service.get_flag(db_session, "cached_flag")
    
    assert flag.key == "cached_flag"
    mock_cache.get_flag.assert_called_with("cached_flag")


def test_get_flag_cache_miss_stores_in_cache(db_session, flag_service, mock_cache):
    """Test that cache miss results in storing flag in cache"""
    # Create flag
    flag_data = FlagCreate(
        key="new_flag",
        name="New Flag",
        enabled=True,
        rollout_percentage=100.0
    )
    created_flag = flag_service.create_flag(db_session, flag_data)
    
    # Reset mock to simulate cache miss on next get
    mock_cache.reset_mock()
    mock_cache.get_flag.return_value = None
    
    # Get flag - cache miss
    flag = flag_service.get_flag(db_session, "new_flag")
    
    assert flag.key == "new_flag"
    # Should have tried to set in cache
    assert mock_cache.set_flag.called


def test_update_flag_invalidates_cache(db_session, flag_service, mock_cache):
    """Test that updating a flag invalidates cache"""
    # Create flag
    flag_data = FlagCreate(
        key="update_test",
        name="Update Test",
        enabled=False,
        rollout_percentage=0.0
    )
    flag_service.create_flag(db_session, flag_data)
    
    # Update flag
    update_data = FlagUpdate(enabled=True, rollout_percentage=100.0)
    flag_service.update_flag(db_session, "update_test", update_data)
    
    # Should have invalidated cache
    mock_cache.invalidate_flag.assert_called_with("update_test")


def test_delete_flag_invalidates_cache(db_session, flag_service, mock_cache):
    """Test that deleting a flag invalidates cache"""
    # Create flag
    flag_data = FlagCreate(
        key="delete_test",
        name="Delete Test",
        enabled=True,
        rollout_percentage=100.0
    )
    flag_service.create_flag(db_session, flag_data)
    
    # Delete flag
    flag_service.delete_flag(db_session, "delete_test")
    
    # Should have invalidated cache
    mock_cache.invalidate_flag.assert_called_with("delete_test")


def test_evaluate_flag_uses_cache(db_session, flag_service, mock_cache):
    """Test that flag evaluation uses cache"""
    # Create flag
    flag_data = FlagCreate(
        key="eval_test",
        name="Eval Test",
        enabled=True,
        rollout_percentage=100.0
    )
    flag_service.create_flag(db_session, flag_data)
    
    # Mock cached evaluation
    mock_cache.get_evaluation.return_value = (True, "Cached result")
    
    # Evaluate
    enabled, reason = flag_service.evaluate_flag(db_session, "eval_test", user_id="user_123")
    
    assert enabled is True
    assert reason == "Cached result"
    mock_cache.get_evaluation.assert_called_once()


def test_evaluate_flag_stores_in_cache(db_session, flag_service, mock_cache):
    """Test that evaluation results are stored in cache"""
    # Create flag
    flag_data = FlagCreate(
        key="eval_cache_test",
        name="Eval Cache Test",
        enabled=True,
        rollout_percentage=100.0
    )
    flag_service.create_flag(db_session, flag_data)
    
    # Reset mocks
    mock_cache.reset_mock()
    mock_cache.get_evaluation.return_value = None  # Cache miss
    
    # Evaluate
    enabled, reason = flag_service.evaluate_flag(db_session, "eval_cache_test", user_id="user_123")
    
    assert enabled is True
    # Should have stored in cache
    mock_cache.set_evaluation.assert_called_once()


def test_flag_service_without_cache_still_works(db_session, flag_service_no_cache):
    """Test that flag service works without cache"""
    # Create flag
    flag_data = FlagCreate(
        key="no_cache_test",
        name="No Cache Test",
        enabled=True,
        rollout_percentage=50.0
    )
    
    flag = flag_service_no_cache.create_flag(db_session, flag_data)
    assert flag.key == "no_cache_test"
    
    # Get flag
    retrieved = flag_service_no_cache.get_flag(db_session, "no_cache_test")
    assert retrieved.key == "no_cache_test"
    
    # Evaluate
    enabled, reason = flag_service_no_cache.evaluate_flag(
        db_session, 
        "no_cache_test", 
        user_id="user_123"
    )
    assert isinstance(enabled, bool)
    assert isinstance(reason, str)


def test_percentage_rollout_deterministic_with_cache(db_session, flag_service, mock_cache):
    """Test that percentage rollout is deterministic even with caching"""
    # Create flag with 50% rollout
    flag_data = FlagCreate(
        key="rollout_test",
        name="Rollout Test",
        enabled=True,
        rollout_percentage=50.0
    )
    flag_service.create_flag(db_session, flag_data)
    
    # Reset cache mock - simulate no cache
    mock_cache.get_evaluation.return_value = None
    
    # Evaluate same user multiple times
    user_id = "consistent_user"
    results = []
    
    for _ in range(5):
        enabled, _ = flag_service.evaluate_flag(db_session, "rollout_test", user_id=user_id)
        results.append(enabled)
    
    # All results should be identical (deterministic)
    assert len(set(results)) == 1


def test_flag_not_found_cached(db_session, flag_service, mock_cache):
    """Test that 'flag not found' result is also cached"""
    mock_cache.get_evaluation.return_value = None  # Cache miss
    
    # Evaluate non-existent flag
    enabled, reason = flag_service.evaluate_flag(db_session, "nonexistent", user_id="user_123")
    
    assert enabled is False
    assert reason == "Flag not found"
    
    # Should cache the negative result
    mock_cache.set_evaluation.assert_called_once()


def test_disabled_flag_cached(db_session, flag_service, mock_cache):
    """Test that disabled flag state is cached"""
    # Create disabled flag
    flag_data = FlagCreate(
        key="disabled_flag",
        name="Disabled Flag",
        enabled=False,
        rollout_percentage=100.0
    )
    flag_service.create_flag(db_session, flag_data)
    
    # Reset mock
    mock_cache.reset_mock()
    mock_cache.get_evaluation.return_value = None
    
    # Evaluate
    enabled, reason = flag_service.evaluate_flag(db_session, "disabled_flag", user_id="user_123")
    
    assert enabled is False
    assert reason == "Flag is disabled"
    
    # Should cache this result
    mock_cache.set_evaluation.assert_called_once()
