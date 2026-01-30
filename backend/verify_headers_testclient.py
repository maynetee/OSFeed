#!/usr/bin/env python3
"""
Script to verify security headers using FastAPI TestClient.
This programmatically verifies what would be seen in browser DevTools.
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from app.main import app

def verify_headers():
    """
    Verify all required security headers are present.
    Simulates Browser DevTools > Network > Headers verification.
    """
    required_headers = [
        "X-Frame-Options",
        "X-Content-Type-Options",
        "Content-Security-Policy",
        "Strict-Transport-Security",
        "Referrer-Policy"
    ]

    print("\n" + "=" * 60)
    print("SECURITY HEADERS VERIFICATION")
    print("=" * 60)
    print("\nSimulating: Browser DevTools > Network > Headers tab")
    print("Endpoint: http://localhost:8000/health\n")

    client = TestClient(app)
    response = client.get("/health")

    print(f"✓ Successfully fetched /health")
    print(f"  Status Code: {response.status_code}\n")

    print("-" * 60)
    print("RESPONSE HEADERS:")
    print("-" * 60)

    missing = []
    for header in required_headers:
        header_lower = header.lower()
        value = response.headers.get(header_lower)
        if value:
            print(f"✓ {header}: {value}")
        else:
            print(f"✗ {header}: MISSING")
            missing.append(header)

    # Also print additional security headers if present
    additional_headers = ["Permissions-Policy"]
    print("\n" + "-" * 60)
    print("ADDITIONAL SECURITY HEADERS:")
    print("-" * 60)
    for header in additional_headers:
        header_lower = header.lower()
        value = response.headers.get(header_lower)
        if value:
            print(f"✓ {header}: {value}")

    print("=" * 60)

    if len(missing) == 0:
        print("\n✓ VERIFICATION PASSED")
        print("\nAll required security headers are present!")
        print("\nThis programmatically verifies what would be seen in:")
        print("  Browser: Open http://localhost:8000/health")
        print("  DevTools: Network tab > Select request > Headers tab")
        print("\nExpected headers present:")
        for header in required_headers:
            print(f"  • {header}")
        return 0
    else:
        print("\n✗ VERIFICATION FAILED")
        print(f"\nMissing headers: {', '.join(missing)}")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(verify_headers())
    except Exception as e:
        print(f"\n✗ Verification error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
