"""
Feature Flag SDK - Usage Examples

This file demonstrates how to use the Feature Flag SDK in your applications.

Prerequisites:
    1. Feature flag service running at http://localhost:8000
    2. SDK installed: pip install -e .
"""

from sdk import FeatureFlagClient, FlagNotFoundError, APIError


def basic_usage():
    """Basic flag evaluation"""
    print("\n=== Basic Usage ===")
    
    # Initialize client
    client = FeatureFlagClient("http://localhost:8000")
    
    # Simple boolean check
    if client.is_enabled("new_checkout_flow", user_id="user_123"):
        print("✓ New checkout flow is enabled for user_123")
    else:
        print("✗ New checkout flow is disabled for user_123")
    
    client.close()


def detailed_evaluation():
    """Get detailed evaluation results"""
    print("\n=== Detailed Evaluation ===")
    
    client = FeatureFlagClient("http://localhost:8000")
    
    # Get full evaluation result with reason
    result = client.evaluate("new_checkout_flow", user_id="user_456")
    
    print(f"Flag: {result.key}")
    print(f"Enabled: {result.enabled}")
    print(f"Reason: {result.reason}")
    
    client.close()


def bulk_evaluation():
    """Evaluate multiple flags at once"""
    print("\n=== Bulk Evaluation ===")
    
    client = FeatureFlagClient("http://localhost:8000")
    
    # Evaluate multiple flags
    flags = ["feature_a", "feature_b", "feature_c", "dark_mode"]
    results = client.evaluate_all(flags, user_id="user_789")
    
    print(f"Evaluated {len(results)} flags:")
    for key, result in results.items():
        status = "✓" if result.enabled else "✗"
        print(f"  {status} {key}: {result.reason}")
    
    client.close()


def context_manager_usage():
    """Using client as context manager (auto-closes)"""
    print("\n=== Context Manager Usage ===")
    
    with FeatureFlagClient("http://localhost:8000") as client:
        enabled = client.is_enabled("experimental_feature", user_id="user_999")
        print(f"Experimental feature enabled: {enabled}")
    
    # Client automatically closed when exiting context


def error_handling():
    """Proper error handling"""
    print("\n=== Error Handling ===")
    
    client = FeatureFlagClient("http://localhost:8000")
    
    # Handle flag not found
    try:
        result = client.evaluate("nonexistent_flag")
        print(f"Flag found: {result.enabled}")
    except FlagNotFoundError as e:
        print(f"✗ Flag not found: {e.flag_key}")
    
    # Handle API errors
    try:
        # This might fail if service is down
        result = client.is_enabled("some_flag")
    except APIError as e:
        print(f"✗ API error {e.status_code}: {e.message}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    client.close()


def caching_example():
    """Demonstrate caching behavior"""
    print("\n=== Caching Example ===")
    
    # Client with caching enabled (default)
    client = FeatureFlagClient(
        "http://localhost:8000",
        enable_cache=True,
        cache_ttl=60  # Cache for 60 seconds
    )
    
    # First call - goes to API
    print("First call (API request)...")
    result1 = client.evaluate("cached_flag", user_id="user_123")
    print(f"  Result: {result1.enabled}")
    
    # Second call - uses cache (much faster!)
    print("Second call (cached)...")
    result2 = client.evaluate("cached_flag", user_id="user_123")
    print(f"  Result: {result2.enabled}")
    
    # Get cache stats
    stats = client.get_cache_stats()
    print(f"Cache stats: {stats}")
    
    client.close()


def management_operations():
    """CRUD operations for managing flags"""
    print("\n=== Management Operations ===")
    
    client = FeatureFlagClient("http://localhost:8000")
    
    # Create a new flag
    print("Creating new flag...")
    try:
        flag = client.create_flag(
            key="sdk_example_flag",
            name="SDK Example Flag",
            description="Created via SDK",
            enabled=True,
            rollout_percentage=50.0
        )
        print(f"✓ Created: {flag.key}")
    except APIError:
        print("Flag already exists, skipping creation")
    
    # Get flag details
    print("\nGetting flag details...")
    flag = client.get_flag("sdk_example_flag")
    print(f"  Key: {flag.key}")
    print(f"  Name: {flag.name}")
    print(f"  Enabled: {flag.enabled}")
    print(f"  Rollout: {flag.rollout_percentage}%")
    
    # Update flag
    print("\nUpdating flag...")
    updated_flag = client.update_flag(
        "sdk_example_flag",
        rollout_percentage=75.0
    )
    print(f"✓ Updated rollout to {updated_flag.rollout_percentage}%")
    
    # List all flags
    print("\nListing all flags...")
    flags = client.list_flags(limit=5)
    print(f"Found {len(flags)} flags:")
    for f in flags:
        print(f"  - {f.key}: {f.name}")
    
    # Delete flag (cleanup)
    print("\nDeleting example flag...")
    client.delete_flag("sdk_example_flag")
    print("✓ Deleted")
    
    client.close()


def custom_configuration():
    """Advanced client configuration"""
    print("\n=== Custom Configuration ===")
    
    # Configure timeout, retries, and caching
    client = FeatureFlagClient(
        base_url="http://localhost:8000",
        timeout=10.0,           # 10 second timeout
        enable_cache=True,      # Enable caching
        cache_ttl=120,          # Cache for 2 minutes
        max_retries=3           # Retry up to 3 times on failure
    )
    
    print(f"Client configured:")
    print(f"  Base URL: {client.base_url}")
    print(f"  Timeout: {client.timeout}s")
    print(f"  Cache enabled: {client.cache_enabled}")
    print(f"  Max retries: {client.max_retries}")
    
    client.close()


def percentage_rollout_example():
    """Demonstrate percentage rollout behavior"""
    print("\n=== Percentage Rollout ===")
    
    client = FeatureFlagClient("http://localhost:8000")
    
    # Assume we have a flag with 50% rollout
    flag_key = "fifty_percent_rollout"
    
    # Test with multiple users
    enabled_count = 0
    total_users = 20
    
    print(f"Testing {flag_key} with {total_users} users...")
    
    for i in range(total_users):
        user_id = f"user_{i}"
        enabled = client.is_enabled(flag_key, user_id=user_id)
        if enabled:
            enabled_count += 1
        
        status = "✓" if enabled else "✗"
        print(f"  {status} {user_id}")
    
    percentage = (enabled_count / total_users) * 100
    print(f"\n{enabled_count}/{total_users} users enabled ({percentage:.1f}%)")
    
    client.close()


def real_world_example():
    """Real-world usage pattern"""
    print("\n=== Real-World Example ===")
    
    # Initialize once at application startup
    flag_client = FeatureFlagClient(
        "http://localhost:8000",
        enable_cache=True,
        cache_ttl=60
    )
    
    def process_checkout(user_id: str):
        """Example checkout function with feature flags"""
        
        # Check if new checkout flow is enabled
        use_new_checkout = flag_client.is_enabled(
            "new_checkout_flow",
            user_id=user_id
        )
        
        if use_new_checkout:
            print(f"  Using new checkout for {user_id}")
            # ... new checkout logic
        else:
            print(f"  Using old checkout for {user_id}")
            # ... old checkout logic
        
        # Check multiple features at once
        features = flag_client.evaluate_all(
            ["express_shipping", "gift_wrapping", "discount_code"],
            user_id=user_id
        )
        
        if features.get("express_shipping", None) and features["express_shipping"].enabled:
            print(f"    ✓ Express shipping available")
        
        if features.get("gift_wrapping", None) and features["gift_wrapping"].enabled:
            print(f"    ✓ Gift wrapping available")
    
    # Simulate processing orders for different users
    print("Processing checkouts:")
    for i in range(3):
        user_id = f"customer_{i}"
        print(f"\n{user_id}:")
        process_checkout(user_id)
    
    flag_client.close()


if __name__ == "__main__":
    """
    Run this script to see all examples.
    
    Make sure the feature flag service is running:
        uvicorn app.main:app --reload
    """
    
    print("=" * 60)
    print("Feature Flag SDK - Usage Examples")
    print("=" * 60)
    
    try:
        basic_usage()
        detailed_evaluation()
        context_manager_usage()
        error_handling()
        caching_example()
        custom_configuration()
        
        # Management examples (requires API to be running)
        # management_operations()
        
        # These require specific flags to exist
        # bulk_evaluation()
        # percentage_rollout_example()
        # real_world_example()
        
        print("\n" + "=" * 60)
        print("✓ All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        print("Make sure the feature flag service is running at http://localhost:8000")