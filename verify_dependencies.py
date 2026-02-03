#!/usr/bin/env python3
"""Verify that all required dependencies are installed and importable."""

import sys
sys.path.insert(0, '/Users/mendel/Library/Python/3.9/lib/python/site-packages')

def verify_dependencies():
    """Check all critical dependencies."""
    results = []

    dependencies = [
        'fastapi',
        'pytest',
        'sqlalchemy',
        'uvicorn',
        'pydantic',
        'asyncpg',
        'alembic',
    ]

    for dep in dependencies:
        try:
            mod = __import__(dep)
            version = getattr(mod, '__version__', 'unknown')
            results.append(f"✓ {dep}: {version}")
        except ImportError as e:
            results.append(f"✗ {dep}: FAILED - {e}")

    return results

if __name__ == '__main__':
    print("=" * 60)
    print("DEPENDENCY VERIFICATION")
    print("=" * 60)
    for result in verify_dependencies():
        print(result)
    print("=" * 60)
