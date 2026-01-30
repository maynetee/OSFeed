#!/usr/bin/env python3
"""Script to run export utils tests."""
import sys
import subprocess

result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/test_export_utils.py', '-v'],
    capture_output=True,
    text=True
)
print(result.stdout)
if result.stderr:
    print(result.stderr, file=sys.stderr)
sys.exit(result.returncode)
