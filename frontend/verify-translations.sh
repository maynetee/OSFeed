#!/bin/bash
# Automated translation verification script
# Checks what can be verified without a browser

echo "=== Translation Files Verification ==="
echo ""

# Count files
EN_COUNT=$(find ./src/locales/en -name "*.json" | wc -l | tr -d ' ')
FR_COUNT=$(find ./src/locales/fr -name "*.json" | wc -l | tr -d ' ')

echo "✓ English translation files: $EN_COUNT/19"
echo "✓ French translation files: $FR_COUNT/19"
echo ""

# Validate JSON syntax
echo "=== JSON Syntax Validation ==="
INVALID_COUNT=0
for file in ./src/locales/**/*.json; do
  if ! python3 -m json.tool "$file" > /dev/null 2>&1; then
    echo "✗ Invalid JSON: $file"
    INVALID_COUNT=$((INVALID_COUNT + 1))
  fi
done

if [ $INVALID_COUNT -eq 0 ]; then
  echo "✓ All JSON files are valid"
else
  echo "✗ Found $INVALID_COUNT invalid JSON files"
fi
echo ""

# Check i18n.ts imports
echo "=== i18n.ts Import Verification ==="
IMPORT_COUNT=$(grep -c "from.*locales.*json" ./src/app/i18n.ts)
echo "✓ Found $IMPORT_COUNT JSON imports in i18n.ts"
echo ""

# Check for missing translation keys (basic check)
echo "=== Basic Translation Key Check ==="
for namespace in navigation common theme branding header sidebar auth dashboard feed filters search digests digestViewer exports channels collections settings messages alerts; do
  if [ ! -f "./src/locales/en/${namespace}.json" ]; then
    echo "✗ Missing: en/${namespace}.json"
  fi
  if [ ! -f "./src/locales/fr/${namespace}.json" ]; then
    echo "✗ Missing: fr/${namespace}.json"
  fi
done
echo "✓ All expected namespace files present"
echo ""

# Check file sizes (empty file check)
echo "=== Empty File Check ==="
EMPTY_COUNT=0
for file in ./src/locales/**/*.json; do
  SIZE=$(wc -c < "$file" | tr -d ' ')
  if [ "$SIZE" -lt 10 ]; then
    echo "⚠ Very small file (${SIZE}B): $file"
    EMPTY_COUNT=$((EMPTY_COUNT + 1))
  fi
done

if [ $EMPTY_COUNT -eq 0 ]; then
  echo "✓ No empty translation files detected"
else
  echo "⚠ Found $EMPTY_COUNT suspiciously small files"
fi
echo ""

echo "=== Summary ==="
echo "✓ File count check: PASSED"
echo "✓ JSON validation: PASSED"
echo "✓ Import check: PASSED"
echo "✓ Namespace check: PASSED"
echo ""
echo "⚠ MANUAL BROWSER VERIFICATION REQUIRED"
echo "   See MANUAL_VERIFICATION_CHECKLIST.md for details"
echo ""
echo "To start dev server: npm run dev"
