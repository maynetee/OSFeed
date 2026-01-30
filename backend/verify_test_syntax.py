#!/usr/bin/env python3
"""Verify test file syntax and imports."""
import sys
import ast

# Check if file can be parsed
try:
    with open('tests/test_export_utils.py', 'r') as f:
        code = f.read()
    ast.parse(code)
    print("✓ Syntax check passed")
except SyntaxError as e:
    print(f"✗ Syntax error: {e}")
    sys.exit(1)

# Try to import the module being tested
sys.path.insert(0, '.')
try:
    from app.utils.export import (
        MESSAGE_CSV_COLUMNS,
        create_csv_writer,
        generate_csv_row,
        generate_html_template,
        generate_html_article,
        generate_pdf_bytes,
        WEASYPRINT_AVAILABLE,
    )
    print("✓ Export utils imports successful")
    print(f"  - MESSAGE_CSV_COLUMNS: {len(MESSAGE_CSV_COLUMNS)} columns")
    print(f"  - WEASYPRINT_AVAILABLE: {WEASYPRINT_AVAILABLE}")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

# Verify functions exist
functions = [
    create_csv_writer,
    generate_csv_row,
    generate_html_template,
    generate_html_article,
    generate_pdf_bytes,
]
print(f"✓ All {len(functions)} functions imported successfully")

print("\n✓ All verification checks passed!")
print("Note: Actual test execution requires pytest to be installed.")
