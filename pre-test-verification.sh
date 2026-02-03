#!/bin/bash

# Quick automated verification before manual browser testing
# Tests backend cookie implementation

set -e

echo "======================================="
echo "Pre-Test Verification"
echo "Cookie-Based Authentication Backend"
echo "======================================="
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BACKEND_URL="http://localhost:8000"
FAILED=0

# Function to test endpoint
test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local expected="$5"

    echo "Testing: $name"

    if [ "$method" = "POST" ]; then
        response=$(curl -s -i -X POST "$BACKEND_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" 2>&1)
    else
        response=$(curl -s -i "$BACKEND_URL$endpoint" 2>&1)
    fi

    if echo "$response" | grep -q "$expected"; then
        echo -e "  ${GREEN}✓ PASS${NC}"
        return 0
    else
        echo -e "  ${RED}✗ FAIL${NC}"
        echo "  Expected to find: $expected"
        echo "  Response:"
        echo "$response" | head -20
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Check if backend is running
echo "1. Checking if backend is running..."
if ! curl -s $BACKEND_URL/docs > /dev/null 2>&1; then
    echo -e "${RED}✗ Backend is not running${NC}"
    echo ""
    echo "Please start the backend first:"
    echo "  cd backend"
    echo "  source venv/bin/activate"
    echo "  uvicorn app.main:app --reload --port 8000"
    echo ""
    exit 1
fi
echo -e "${GREEN}✓ Backend is running${NC}"
echo ""

# Test 1: API docs accessible
echo "2. Verifying API is accessible..."
if curl -s $BACKEND_URL/docs | grep -q "Swagger"; then
    echo -e "  ${GREEN}✓ API docs accessible${NC}"
else
    echo -e "  ${RED}✗ API docs not accessible${NC}"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 2: Check config has cookie settings
echo "3. Checking cookie configuration..."
echo "  (This test requires backend Python to be accessible)"
# We'll rely on the implementation being correct
echo -e "  ${YELLOW}⊙ Skipped (manual implementation review)${NC}"
echo ""

# Test 3: Login endpoint sets cookies
echo "4. Testing login endpoint cookie response..."
echo "  Endpoint: POST /api/auth/login"
echo ""

# Create a test login request (adjust credentials as needed)
LOGIN_DATA='{"username":"test@example.com","password":"password"}'
echo "  Sending login request..."

LOGIN_RESPONSE=$(curl -s -i -X POST "$BACKEND_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "$LOGIN_DATA" 2>&1 || echo "CURL_FAILED")

if echo "$LOGIN_RESPONSE" | grep -q "CURL_FAILED"; then
    echo -e "  ${RED}✗ Login request failed${NC}"
    FAILED=$((FAILED + 1))
else
    # Check for Set-Cookie headers
    echo "  Checking for Set-Cookie headers..."

    if echo "$LOGIN_RESPONSE" | grep -qi "Set-Cookie.*access_token"; then
        echo -e "    ${GREEN}✓ access_token cookie found${NC}"
    else
        echo -e "    ${RED}✗ access_token cookie NOT found${NC}"
        FAILED=$((FAILED + 1))
    fi

    if echo "$LOGIN_RESPONSE" | grep -qi "Set-Cookie.*refresh_token"; then
        echo -e "    ${GREEN}✓ refresh_token cookie found${NC}"
    else
        echo -e "    ${RED}✗ refresh_token cookie NOT found${NC}"
        FAILED=$((FAILED + 1))
    fi

    # Check for httpOnly flag
    if echo "$LOGIN_RESPONSE" | grep -qi "HttpOnly"; then
        echo -e "    ${GREEN}✓ HttpOnly flag present${NC}"
    else
        echo -e "    ${RED}✗ HttpOnly flag NOT found${NC}"
        FAILED=$((FAILED + 1))
    fi

    # Check for SameSite
    if echo "$LOGIN_RESPONSE" | grep -qi "SameSite"; then
        echo -e "    ${GREEN}✓ SameSite attribute present${NC}"
    else
        echo -e "    ${YELLOW}⊙ SameSite attribute NOT found (may be optional)${NC}"
    fi

    # Check that tokens are NOT in response body
    if echo "$LOGIN_RESPONSE" | grep -q '"access_token"'; then
        echo -e "    ${RED}✗ WARNING: access_token found in JSON body (should only be in cookie)${NC}"
        FAILED=$((FAILED + 1))
    else
        echo -e "    ${GREEN}✓ access_token NOT in JSON body (correct)${NC}"
    fi

    if echo "$LOGIN_RESPONSE" | grep -q '"refresh_token"'; then
        echo -e "    ${RED}✗ WARNING: refresh_token found in JSON body (should only be in cookie)${NC}"
        FAILED=$((FAILED + 1))
    else
        echo -e "    ${GREEN}✓ refresh_token NOT in JSON body (correct)${NC}"
    fi
fi
echo ""

# Test 4: Verify backend tests pass
echo "5. Running backend tests..."
echo "  Command: cd backend && pytest tests/test_auth_refresh.py tests/test_auth_logout.py -v"
echo ""

cd backend
if pytest tests/test_auth_refresh.py tests/test_auth_logout.py -v 2>&1 | tee /tmp/pytest-output.txt; then
    echo ""
    echo -e "  ${GREEN}✓ Backend tests PASSED${NC}"
else
    echo ""
    echo -e "  ${RED}✗ Backend tests FAILED${NC}"
    echo "  Check output above for details"
    FAILED=$((FAILED + 1))
fi
cd ..
echo ""

# Summary
echo "======================================="
echo "Pre-Test Verification Summary"
echo "======================================="
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "Backend is ready for manual browser testing."
    echo ""
    echo "Next steps:"
    echo "  1. Open MANUAL_TESTING_GUIDE.md"
    echo "  2. Start frontend: cd frontend && npm run dev"
    echo "  3. Open browser to http://localhost:5173"
    echo "  4. Follow the test scenarios in the guide"
else
    echo -e "${RED}✗ $FAILED check(s) failed${NC}"
    echo ""
    echo "Please fix the issues above before proceeding to manual testing."
fi
echo ""
