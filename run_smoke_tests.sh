#!/bin/bash

# Smoke Test Verification Script for Subtask 2-3
# Purpose: Run frontend smoke tests to verify functionality without 'unsafe-eval'

set -e  # Exit on error

echo "=================================================="
echo "Frontend Smoke Test Verification"
echo "Subtask: subtask-2-3"
echo "=================================================="
echo ""

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo "❌ ERROR: Node.js is not installed"
    echo "   Please install Node.js (v18 or higher) from https://nodejs.org"
    exit 1
fi

echo "✓ Node.js found: $(node --version)"

# Check for npm
if ! command -v npm &> /dev/null; then
    echo "❌ ERROR: npm is not installed"
    exit 1
fi

echo "✓ npm found: $(npm --version)"
echo ""

# Navigate to frontend directory
cd frontend || {
    echo "❌ ERROR: frontend directory not found"
    exit 1
}

echo "📁 Working directory: $(pwd)"
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    echo "✓ Dependencies installed"
    echo ""
fi

# Check if Playwright is installed
if [ ! -d "node_modules/@playwright" ]; then
    echo "🎭 Installing Playwright..."
    npm install --save-dev @playwright/test
    echo "✓ Playwright installed"
    echo ""
fi

# Install Playwright browsers if needed
if ! npx playwright --version &> /dev/null; then
    echo "🌐 Installing Playwright browsers..."
    npx playwright install
    echo "✓ Browsers installed"
    echo ""
fi

echo "=================================================="
echo "Running Smoke Tests"
echo "=================================================="
echo ""
echo "Test file: tests/smoke.spec.ts"
echo "Tests to run:"
echo "  1. Login flow reaches dashboard"
echo "  2. Navigation to feed opens export dialog"
echo "  3. Search page shows tabs"
echo ""

# Run smoke tests
echo "🧪 Executing tests..."
echo ""

if npm run test:e2e -- tests/smoke.spec.ts --reporter=list; then
    echo ""
    echo "=================================================="
    echo "✅ SUCCESS: All smoke tests passed!"
    echo "=================================================="
    echo ""
    echo "Results:"
    echo "  ✓ Login flow works correctly"
    echo "  ✓ Navigation and UI components function properly"
    echo "  ✓ No CSP violations detected"
    echo "  ✓ Frontend works without 'unsafe-eval' in CSP"
    echo ""
    echo "Next steps:"
    echo "  1. Review test output above for any warnings"
    echo "  2. Mark subtask-2-3 as completed"
    echo "  3. Commit changes"
    echo ""
    exit 0
else
    echo ""
    echo "=================================================="
    echo "❌ FAILURE: Smoke tests failed!"
    echo "=================================================="
    echo ""
    echo "Possible causes:"
    echo "  • CSP violations due to 'unsafe-eval' removal"
    echo "  • Component rendering issues"
    echo "  • Backend not running (if tests need API)"
    echo "  • Environment configuration problems"
    echo ""
    echo "Debugging steps:"
    echo "  1. Check test output above for specific errors"
    echo "  2. Run with debug mode: npx playwright test tests/smoke.spec.ts --debug"
    echo "  3. Run with headed mode: npx playwright test tests/smoke.spec.ts --headed"
    echo "  4. Check browser console for CSP violations"
    echo "  5. Review SMOKE_TEST_VERIFICATION_GUIDE.md for troubleshooting"
    echo ""
    exit 1
fi
