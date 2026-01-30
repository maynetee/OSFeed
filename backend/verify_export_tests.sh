#!/bin/bash
# Verification script for export tests after refactoring
# This script runs the export tests to ensure the refactored code works correctly

set -e

echo "=========================================="
echo "Export Tests Verification"
echo "=========================================="
echo ""
echo "Verifying that refactored export utilities are used correctly..."
echo ""

# Check that export utilities exist
echo "✓ Checking export utilities module..."
python3 -c "import sys; sys.path.insert(0, '.'); from app.utils.export import generate_csv_row, generate_html_template, generate_pdf_bytes, MESSAGE_CSV_COLUMNS, create_csv_writer, generate_html_article; print('  Export utilities import successfully')" || exit 1

# Check that collections.py imports the utilities
echo "✓ Checking collections.py imports export utilities..."
grep -q "from app.utils.export import" app/api/collections.py && echo "  Collections.py uses export utilities" || exit 1

# Check that collections.py uses the utilities
echo "✓ Verifying utility usage in collections.py..."
grep -q "create_csv_writer()" app/api/collections.py && echo "  - create_csv_writer() used" || exit 1
grep -q "generate_csv_row" app/api/collections.py && echo "  - generate_csv_row() used" || exit 1
grep -q "generate_html_template" app/api/collections.py && echo "  - generate_html_template() used" || exit 1
grep -q "generate_html_article" app/api/collections.py && echo "  - generate_html_article() used" || exit 1
grep -q "generate_pdf_bytes" app/api/collections.py && echo "  - generate_pdf_bytes() used" || exit 1
grep -q "MESSAGE_CSV_COLUMNS" app/api/collections.py && echo "  - MESSAGE_CSV_COLUMNS used" || exit 1

echo ""
echo "✓ All refactored utilities are properly integrated!"
echo ""
echo "=========================================="
echo "Running Export Tests"
echo "=========================================="
echo ""

# Run the actual tests
# Note: pytest may need to be installed first
if command -v pytest &> /dev/null; then
    pytest tests/test_export.py -v
elif python3 -m pytest --version &> /dev/null 2>&1; then
    python3 -m pytest tests/test_export.py -v
else
    echo "⚠ pytest not found. Install it with: pip install pytest pytest-asyncio"
    echo ""
    echo "To run tests manually:"
    echo "  cd backend"
    echo "  pip install -r requirements.txt"
    echo "  pytest tests/test_export.py -v"
    exit 1
fi

echo ""
echo "=========================================="
echo "✓ All verification checks passed!"
echo "=========================================="
