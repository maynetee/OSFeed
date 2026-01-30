#!/bin/bash
# Script to verify security headers using curl
# This demonstrates what would be seen in Browser DevTools

echo "=========================================="
echo "Security Headers Verification with curl"
echo "=========================================="
echo ""
echo "Note: This requires the backend server to be running:"
echo "  uvicorn app.main:app --reload"
echo ""
echo "Fetching headers from http://localhost:8000/health..."
echo ""

# Use curl to fetch headers
curl -I http://localhost:8000/health 2>&1

echo ""
echo "=========================================="
echo "Expected Security Headers:"
echo "=========================================="
echo "✓ X-Frame-Options: DENY"
echo "✓ X-Content-Type-Options: nosniff"
echo "✓ Content-Security-Policy: [CSP policy]"
echo "✓ Strict-Transport-Security: max-age=31536000; includeSubDomains"
echo "✓ Referrer-Policy: strict-origin-when-cross-origin"
echo "✓ Permissions-Policy: [permissions restrictions]"
echo ""
echo "This is equivalent to:"
echo "  Browser DevTools > Network > Headers tab"
echo ""
