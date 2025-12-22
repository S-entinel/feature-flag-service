import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db, get_cache_service
from app.models.flag import Base
from app.services.cache_service import CacheService

# Test database
TEST_DATABASE_URL = "sqlite:///./test_flags.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


def override_get_cache_service():
    """Override cache service to disable caching in tests"""
    return CacheService(redis_client=None)


# Override dependencies
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_cache_service] = override_get_cache_service

# Create test client
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test, drop after"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_create_flag():
    """Test creating a feature flag"""
    response = client.post(
        "/flags/",
        json={
            "key": "test_feature",
            "name": "Test Feature",
            "description": "A test feature flag",
            "enabled": True,
            "rollout_percentage": 50.0
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["key"] == "test_feature"
    assert data["name"] == "Test Feature"
    assert data["enabled"] is True
    assert data["rollout_percentage"] == 50.0


def test_create_duplicate_flag():
    """Test that duplicate keys are rejected"""
    flag_data = {
        "key": "duplicate",
        "name": "Duplicate Flag",
        "enabled": False,
        "rollout_percentage": 100.0
    }
    
    # First creation should succeed
    response1 = client.post("/flags/", json=flag_data)
    assert response1.status_code == 201
    
    # Second should fail
    response2 = client.post("/flags/", json=flag_data)
    assert response2.status_code == 400


def test_get_flag():
    """Test retrieving a flag"""
    # Create a flag first
    client.post(
        "/flags/",
        json={
            "key": "get_test",
            "name": "Get Test",
            "enabled": True,
            "rollout_percentage": 100.0
        }
    )
    
    # Retrieve it
    response = client.get("/flags/get_test")
    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "get_test"


def test_get_nonexistent_flag():
    """Test retrieving a flag that doesn't exist"""
    response = client.get("/flags/nonexistent")
    assert response.status_code == 404


def test_list_flags():
    """Test listing all flags"""
    # Create multiple flags
    for i in range(3):
        client.post(
            "/flags/",
            json={
                "key": f"flag_{i}",
                "name": f"Flag {i}",
                "enabled": True,
                "rollout_percentage": 100.0
            }
        )
    
    # List all
    response = client.get("/flags/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


def test_update_flag():
    """Test updating a flag"""
    # Create a flag
    client.post(
        "/flags/",
        json={
            "key": "update_test",
            "name": "Update Test",
            "enabled": False,
            "rollout_percentage": 0.0
        }
    )
    
    # Update it
    response = client.put(
        "/flags/update_test",
        json={
            "enabled": True,
            "rollout_percentage": 75.0
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["enabled"] is True
    assert data["rollout_percentage"] == 75.0


def test_delete_flag():
    """Test deleting a flag"""
    # Create a flag
    client.post(
        "/flags/",
        json={
            "key": "delete_test",
            "name": "Delete Test",
            "enabled": True,
            "rollout_percentage": 100.0
        }
    )
    
    # Delete it
    response = client.delete("/flags/delete_test")
    assert response.status_code == 204
    
    # Verify it's gone
    response = client.get("/flags/delete_test")
    assert response.status_code == 404


def test_evaluate_flag_enabled():
    """Test evaluating an enabled flag"""
    # Create an enabled flag
    client.post(
        "/flags/",
        json={
            "key": "eval_test",
            "name": "Eval Test",
            "enabled": True,
            "rollout_percentage": 100.0
        }
    )
    
    # Evaluate it
    response = client.get("/flags/eval_test/evaluate")
    assert response.status_code == 200
    data = response.json()
    assert data["enabled"] is True


def test_evaluate_flag_disabled():
    """Test evaluating a disabled flag"""
    # Create a disabled flag
    client.post(
        "/flags/",
        json={
            "key": "disabled_test",
            "name": "Disabled Test",
            "enabled": False,
            "rollout_percentage": 100.0
        }
    )
    
    # Evaluate it
    response = client.get("/flags/disabled_test/evaluate")
    assert response.status_code == 200
    data = response.json()
    assert data["enabled"] is False


def test_evaluate_flag_percentage_rollout():
    """Test percentage-based rollout"""
    # Create a flag with 50% rollout
    client.post(
        "/flags/",
        json={
            "key": "rollout_test",
            "name": "Rollout Test",
            "enabled": True,
            "rollout_percentage": 50.0
        }
    )
    
    # Test with multiple user IDs
    enabled_count = 0
    total_users = 100
    
    for i in range(total_users):
        response = client.get(f"/flags/rollout_test/evaluate?user_id=user_{i}")
        data = response.json()
        if data["enabled"]:
            enabled_count += 1
    
    # Should be approximately 50% (allow some variance)
    assert 40 <= enabled_count <= 60


def test_percentage_rollout_deterministic():
    """Test that same user always gets same result"""
    # Create a flag
    client.post(
        "/flags/",
        json={
            "key": "deterministic_test",
            "name": "Deterministic Test",
            "enabled": True,
            "rollout_percentage": 50.0
        }
    )
    
    # Evaluate multiple times with same user_id
    user_id = "user_123"
    results = []
    
    for _ in range(5):
        response = client.get(f"/flags/deterministic_test/evaluate?user_id={user_id}")
        data = response.json()
        results.append(data["enabled"])
    
    # All results should be the same
    assert len(set(results)) == 1
