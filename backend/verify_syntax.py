#!/usr/bin/env python3
"""Verify Python syntax of all refactored files."""
import py_compile
import sys

files_to_check = [
    "app/api/messages.py",
    "app/services/message_utils.py",
    "app/services/message_streaming_service.py",
    "app/services/message_export_service.py",
    "app/services/message_translation_bulk_service.py",
    "app/services/message_media_service.py",
]

def verify_syntax():
    """Check Python syntax of all files."""
    all_passed = True

    for file_path in files_to_check:
        try:
            py_compile.compile(file_path, doraise=True)
            print(f"✓ {file_path} - syntax valid")
        except py_compile.PyCompileError as e:
            print(f"✗ {file_path} - syntax error:")
            print(f"  {e}")
            all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("✓ All files have valid Python syntax!")
        print("="*60)
        return 0
    else:
        print("✗ Some files have syntax errors")
        print("="*60)
        return 1

if __name__ == "__main__":
    sys.exit(verify_syntax())
