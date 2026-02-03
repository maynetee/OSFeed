#!/usr/bin/env python3
"""Verify all refactored modules import successfully."""
import sys
sys.path.insert(0, '.')

def verify_imports():
    """Test that all refactored modules can be imported."""
    try:
        print("Checking messages.py...")
        from app.api.messages import router
        print("✓ messages.py imports successfully")

        print("\nChecking message_utils.py...")
        from app.services.message_utils import apply_message_filters, message_to_response, get_similar_messages
        print("✓ message_utils.py imports successfully")

        print("\nChecking message_streaming_service.py...")
        from app.services.message_streaming_service import create_message_stream
        print("✓ message_streaming_service.py imports successfully")

        print("\nChecking message_export_service.py...")
        from app.services.message_export_service import export_messages_csv, export_messages_html, export_messages_pdf
        print("✓ message_export_service.py imports successfully")

        print("\nChecking message_translation_bulk_service.py...")
        from app.services.message_translation_bulk_service import translate_messages_batch, translate_single_message
        print("✓ message_translation_bulk_service.py imports successfully")

        print("\nChecking message_media_service.py...")
        from app.services.message_media_service import get_media_stream
        print("✓ message_media_service.py imports successfully")

        print("\n" + "="*60)
        print("✓ All refactored modules import successfully!")
        print("="*60)
        return 0

    except Exception as e:
        print(f"\n✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(verify_imports())
