#!/bin/bash
# Automated End-to-End Cookie Authentication Testing
# Tests the complete auth flow using curl commands

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BACKEND_URL="http://localhost:8000"
COOKIE_JAR="/tmp/osfeed-test-cookies.txt"
FAILED=0

echo "======================================="
echo "Automated E2E Cookie Authentication Test"
echo "======================================="
echo ""

# Clean up cookie jar
rm -f "$COOKIE_JAR"

# Test credentials
TEST_EMAIL="test@example.com"
TEST_PASSWORD="password"

echo -e "${BLUE}Test 1: Backend Unit Tests${NC}"
echo "Running pytest for auth tests..."
cd backend && ./venv/bin/python -m pytest tests/test_auth_refresh.py tests/test_auth_logout.py -v 2>&1 | tail -20
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo -e "${GREEN}✓ All backend unit tests passed${NC}"
else
    echo -e "${RED}✗ Backend unit tests failed${NC}"
    FAILED=$((FAILED + 1))
fi
cd ..
echo ""

echo -e "${BLUE}Test 2: Login and Cookie Verification${NC}"
echo "POST /api/auth/login"

LOGIN_RESPONSE=$(curl -s -i -X POST "$BACKEND_URL/api/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$TEST_EMAIL&password=$TEST_PASSWORD" \
    -c "$COOKIE_JAR" 2>&1)

if echo "$LOGIN_RESPONSE" | grep -q "HTTP/.* 200"; then
    echo -e "${GREEN}✓ Login successful (200 OK)${NC}"
else
    echo -e "${RED}✗ Login failed${NC}"
    echo "$LOGIN_RESPONSE" | head -20
    FAILED=$((FAILED + 1))
fi

# Check for Set-Cookie headers
if echo "$LOGIN_RESPONSE" | grep -qi "Set-Cookie.*access_token"; then
    echo -e "${GREEN}✓ access_token cookie set${NC}"
else
    echo -e "${RED}✗ access_token cookie NOT set${NC}"
    FAILED=$((FAILED + 1))
fi

if echo "$LOGIN_RESPONSE" | grep -qi "Set-Cookie.*refresh_token"; then
    echo -e "${GREEN}✓ refresh_token cookie set${NC}"
else
    echo -e "${RED}✗ refresh_token cookie NOT set${NC}"
    FAILED=$((FAILED + 1))
fi

# Check for HttpOnly flag
if echo "$LOGIN_RESPONSE" | grep -qi "HttpOnly"; then
    echo -e "${GREEN}✓ HttpOnly flag present${NC}"
else
    echo -e "${RED}✗ HttpOnly flag NOT present${NC}"
    FAILED=$((FAILED + 1))
fi

# Check for SameSite
if echo "$LOGIN_RESPONSE" | grep -qi "SameSite"; then
    echo -e "${GREEN}✓ SameSite attribute present${NC}"
else
    echo -e "${YELLOW}⊙ SameSite attribute not found (may be optional)${NC}"
fi

# Verify tokens NOT in JSON response body
if echo "$LOGIN_RESPONSE" | grep -q '"access_token"'; then
    echo -e "${RED}✗ WARNING: access_token found in JSON body${NC}"
    FAILED=$((FAILED + 1))
else
    echo -e "${GREEN}✓ access_token NOT in JSON body (correct)${NC}"
fi

if echo "$LOGIN_RESPONSE" | grep -q '"refresh_token"'; then
    echo -e "${RED}✗ WARNING: refresh_token found in JSON body${NC}"
    FAILED=$((FAILED + 1))
else
    echo -e "${GREEN}✓ refresh_token NOT in JSON body (correct)${NC}"
fi

# Verify user info IS in JSON response
if echo "$LOGIN_RESPONSE" | grep -q '"user"'; then
    echo -e "${GREEN}✓ User info present in JSON response${NC}"
else
    echo -e "${RED}✗ User info NOT in JSON response${NC}"
    FAILED=$((FAILED + 1))
fi

echo ""

echo -e "${BLUE}Test 3: Protected Endpoint Access with Cookies${NC}"
echo "GET /api/users/me (requires authentication)"

# Make authenticated request using cookies
ME_RESPONSE=$(curl -s -i -X GET "$BACKEND_URL/api/users/me" \
    -b "$COOKIE_JAR" 2>&1)

if echo "$ME_RESPONSE" | grep -q "HTTP/.* 200"; then
    echo -e "${GREEN}✓ Protected endpoint accessible with cookies${NC}"
else
    echo -e "${RED}✗ Protected endpoint returned error${NC}"
    echo "$ME_RESPONSE" | head -20
    FAILED=$((FAILED + 1))
fi

# Verify response contains user data
if echo "$ME_RESPONSE" | grep -q '"email"'; then
    echo -e "${GREEN}✓ User data returned from protected endpoint${NC}"
else
    echo -e "${RED}✗ No user data in response${NC}"
    FAILED=$((FAILED + 1))
fi

echo ""

echo -e "${BLUE}Test 4: Refresh Token Flow${NC}"
echo "POST /api/auth/refresh"

REFRESH_RESPONSE=$(curl -s -i -X POST "$BACKEND_URL/api/auth/refresh" \
    -b "$COOKIE_JAR" \
    -c "$COOKIE_JAR" 2>&1)

if echo "$REFRESH_RESPONSE" | grep -q "HTTP/.* 200"; then
    echo -e "${GREEN}✓ Token refresh successful${NC}"
else
    echo -e "${RED}✗ Token refresh failed${NC}"
    echo "$REFRESH_RESPONSE" | head -20
    FAILED=$((FAILED + 1))
fi

# Verify new tokens set in cookies
if echo "$REFRESH_RESPONSE" | grep -qi "Set-Cookie.*access_token"; then
    echo -e "${GREEN}✓ New access_token cookie set${NC}"
else
    echo -e "${RED}✗ New access_token cookie NOT set${NC}"
    FAILED=$((FAILED + 1))
fi

if echo "$REFRESH_RESPONSE" | grep -qi "Set-Cookie.*refresh_token"; then
    echo -e "${GREEN}✓ New refresh_token cookie set${NC}"
else
    echo -e "${RED}✗ New refresh_token cookie NOT set${NC}"
    FAILED=$((FAILED + 1))
fi

echo ""

echo -e "${BLUE}Test 5: Logout and Cookie Clearing${NC}"
echo "POST /api/auth/logout"

LOGOUT_RESPONSE=$(curl -s -i -X POST "$BACKEND_URL/api/auth/logout" \
    -b "$COOKIE_JAR" 2>&1)

if echo "$LOGOUT_RESPONSE" | grep -q "HTTP/.* 200"; then
    echo -e "${GREEN}✓ Logout successful${NC}"
else
    echo -e "${RED}✗ Logout failed${NC}"
    echo "$LOGOUT_RESPONSE" | head -20
    FAILED=$((FAILED + 1))
fi

if echo "$LOGOUT_RESPONSE" | grep -q "Successfully logged out"; then
    echo -e "${GREEN}✓ Logout message confirmed${NC}"
else
    echo -e "${RED}✗ Logout message not found${NC}"
    FAILED=$((FAILED + 1))
fi

echo ""

echo -e "${BLUE}Test 6: Verify Cannot Access Protected Endpoint After Logout${NC}"
echo "GET /api/users/me (should fail after logout)"

# Try to access protected endpoint after logout
POST_LOGOUT_RESPONSE=$(curl -s -i -X GET "$BACKEND_URL/api/users/me" \
    -b "$COOKIE_JAR" 2>&1)

if echo "$POST_LOGOUT_RESPONSE" | grep -q "HTTP/.* 401"; then
    echo -e "${GREEN}✓ Protected endpoint correctly returns 401 after logout${NC}"
else
    echo -e "${RED}✗ Protected endpoint did not return 401 after logout${NC}"
    echo "$POST_LOGOUT_RESPONSE" | head -20
    FAILED=$((FAILED + 1))
fi

echo ""

# Summary
echo "======================================="
echo "Test Summary"
echo "======================================="
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED!${NC}"
    echo ""
    echo "Cookie-based authentication is working correctly:"
    echo "  • Tokens stored in httpOnly cookies (not accessible to JavaScript)"
    echo "  • Tokens NOT in JSON response body"
    echo "  • Automatic cookie transmission works"
    echo "  • Token refresh flow works with cookies"
    echo "  • Logout properly clears authentication"
    echo "  • Protected endpoints require valid cookies"
    echo ""
    exit 0
else
    echo -e "${RED}✗ $FAILED test(s) FAILED${NC}"
    echo ""
    echo "Please review the failures above and fix before proceeding."
    echo ""
    exit 1
fi
