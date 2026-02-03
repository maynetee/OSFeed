#!/usr/bin/env python3
"""Comprehensive verification of all refactored modules."""

import sys
import os

# Add user site-packages for dependencies
sys.path.insert(0, '/Users/mendel/Library/Python/3.9/lib/python/site-packages')
# Add backend directory to Python path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, backend_dir)

def verify_all_modules():
    """Verify all refactored modules and their key functions."""
    results = []

    # Test 1: Main API module
    try:
        from app.api import messages
        results.append("✓ app.api.messages: SUCCESS")
    except Exception as e:
        results.append(f"✗ app.api.messages: FAILED - {type(e).__name__}: {str(e)[:80]}")

    # Test 2: Message utils service
    try:
        from app.services import message_utils
        # Check that key functions exist
        assert hasattr(message_utils, 'apply_message_filters')
        assert hasattr(message_utils, 'message_to_response')
        assert hasattr(message_utils, 'get_similar_messages')
        results.append("✓ app.services.message_utils: SUCCESS (all functions present)")
    except Exception as e:
        results.append(f"✗ app.services.message_utils: FAILED - {type(e).__name__}: {str(e)[:80]}")

    # Test 3: Streaming service
    try:
        from app.services import message_streaming_service
        assert hasattr(message_streaming_service, 'create_message_stream')
        results.append("✓ app.services.message_streaming_service: SUCCESS")
    except Exception as e:
        results.append(f"✗ app.services.message_streaming_service: FAILED - {type(e).__name__}: {str(e)[:80]}")

    # Test 4: Export service
    try:
        from app.services import message_export_service
        assert hasattr(message_export_service, 'export_messages_csv')
        assert hasattr(message_export_service, 'export_messages_html')
        assert hasattr(message_export_service, 'export_messages_pdf')
        results.append("✓ app.services.message_export_service: SUCCESS (all export functions present)")
    except Exception as e:
        results.append(f"✗ app.services.message_export_service: FAILED - {type(e).__name__}: {str(e)[:80]}")

    # Test 5: Translation bulk service
    try:
        from app.services import message_translation_bulk_service
        assert hasattr(message_translation_bulk_service, 'translate_messages_batch')
        assert hasattr(message_translation_bulk_service, 'translate_single_message')
        results.append("✓ app.services.message_translation_bulk_service: SUCCESS")
    except Exception as e:
        results.append(f"✗ app.services.message_translation_bulk_service: FAILED - {type(e).__name__}: {str(e)[:80]}")

    # Test 6: Media service
    try:
        from app.services import message_media_service
        assert hasattr(message_media_service, 'get_media_stream')
        results.append("✓ app.services.message_media_service: SUCCESS")
    except Exception as e:
        results.append(f"✗ app.services.message_media_service: FAILED - {type(e).__name__}: {str(e)[:80]}")

    return results

if __name__ == '__main__':
    print("=" * 70)
    print("COMPREHENSIVE REFACTORED MODULE VERIFICATION")
    print("=" * 70)
    print()

    results = verify_all_modules()

    for result in results:
        print(result)

    print()
    print("=" * 70)

    # Check if all passed
    failed = [r for r in results if '✗' in r]
    if failed:
        print(f"RESULT: {len(failed)} FAILED, {len(results) - len(failed)} PASSED")
        sys.exit(1)
    else:
        print(f"RESULT: ALL {len(results)} MODULES PASSED ✓")
        sys.exit(0)
