#!/usr/bin/env python3
"""Verify that all refactored modules can be imported without errors."""

import sys
sys.path.insert(0, '/Users/mendel/Library/Python/3.9/lib/python/site-packages')

def verify_imports():
    """Check all refactored modules."""
    results = []

    modules = [
        'app.api.messages',
        'app.services.message_utils',
        'app.services.message_streaming_service',
        'app.services.message_export_service',
        'app.services.message_translation_bulk_service',
        'app.services.message_media_service',
    ]

    for module in modules:
        try:
            __import__(module)
            results.append(f"✓ {module}: SUCCESS")
        except Exception as e:
            results.append(f"✗ {module}: FAILED - {type(e).__name__}: {e}")

    return results

if __name__ == '__main__':
    print("=" * 60)
    print("REFACTORED MODULE IMPORT VERIFICATION")
    print("=" * 60)
    for result in verify_imports():
        print(result)
    print("=" * 60)
