#!/usr/bin/env python3
"""
Manual verification script for subtask-1-1:
Verify get_auth_rate_limiter() raises RuntimeError when Redis not configured
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Clear REDIS_URL from environment to simulate it not being configured
if 'REDIS_URL' in os.environ:
    del os.environ['REDIS_URL']

# Force settings reload by clearing cache before import
from app.config import get_settings
get_settings.cache_clear()

# Clear the singleton to force reinitialization
import app.services.auth_rate_limiter
app.services.auth_rate_limiter._auth_rate_limiter = None

# Now try to get the auth rate limiter
try:
    from app.services.auth_rate_limiter import get_auth_rate_limiter
    limiter = get_auth_rate_limiter()
    print("❌ FAILED: Expected RuntimeError but get_auth_rate_limiter() succeeded")
    print(f"   Returned: {limiter}")
    sys.exit(1)
except RuntimeError as e:
    error_message = str(e)
    if "REDIS_URL not configured" in error_message:
        print("✅ PASSED: get_auth_rate_limiter() correctly raises RuntimeError")
        print(f"   Error message: {error_message}")
        sys.exit(0)
    else:
        print("❌ FAILED: RuntimeError raised but with wrong message")
        print(f"   Expected message to contain: 'REDIS_URL not configured'")
        print(f"   Actual message: {error_message}")
        sys.exit(1)
except Exception as e:
    print(f"❌ FAILED: Wrong exception type raised: {type(e).__name__}")
    print(f"   Message: {e}")
    sys.exit(1)
