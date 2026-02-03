#!/bin/bash
#
# Manual Verification Script: Role Escalation Attack Prevention
#
# This script performs manual testing of the role escalation vulnerability fix.
# It attempts various privilege escalation attacks and verifies they are all blocked.
#
# Prerequisites:
# - Backend server must be running on http://localhost:8000
# - curl and jq must be installed
#
# Usage:
#   ./verify_role_escalation_fix.sh
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Base URL
BASE_URL="${BASE_URL:-http://localhost:8000}"
API_URL="${BASE_URL}/api"

# Track test results
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to print colored output
print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✅ PASS${NC}: $message"
        ((TESTS_PASSED++))
    elif [ "$status" = "FAIL" ]; then
        echo -e "${RED}❌ FAIL${NC}: $message"
        ((TESTS_FAILED++))
    elif [ "$status" = "INFO" ]; then
        echo -e "${BLUE}ℹ️  INFO${NC}: $message"
    elif [ "$status" = "WARN" ]; then
        echo -e "${YELLOW}⚠️  WARN${NC}: $message"
    fi
}

# Helper function to check if jq is installed
check_jq() {
    if ! command -v jq &> /dev/null; then
        print_status "WARN" "jq is not installed. Install it for better output: brew install jq"
        return 1
    fi
    return 0
}

HAS_JQ=false
if check_jq; then
    HAS_JQ=true
fi

# Helper function to extract JSON field
get_json_field() {
    local json=$1
    local field=$2
    if [ "$HAS_JQ" = true ]; then
        echo "$json" | jq -r ".$field"
    else
        # Fallback regex parsing (less reliable)
        echo "$json" | grep -o "\"$field\":\"[^\"]*\"" | cut -d'"' -f4
    fi
}

echo "========================================="
echo "Role Escalation Vulnerability Fix Test"
echo "========================================="
echo ""

# Step 1: Check server health
print_status "INFO" "Step 1: Checking server health at $API_URL/health"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/health")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n 1)
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    print_status "PASS" "Server is healthy"
else
    print_status "FAIL" "Server health check failed (HTTP $HTTP_CODE)"
    echo "Response: $HEALTH_BODY"
    exit 1
fi
echo ""

# Step 2: Attempt admin role escalation
print_status "INFO" "Step 2: Attempting to register with role=admin"
REGISTER_ADMIN_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/auth/register" \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "attacker-admin-'"$(date +%s)"'@test.com",
    "password": "Attack123!",
    "role": "admin"
  }')

HTTP_CODE=$(echo "$REGISTER_ADMIN_RESPONSE" | tail -n 1)
REGISTER_BODY=$(echo "$REGISTER_ADMIN_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "201" ] || [ "$HTTP_CODE" = "200" ]; then
    ROLE=$(get_json_field "$REGISTER_BODY" "role")
    IS_SUPERUSER=$(get_json_field "$REGISTER_BODY" "is_superuser")

    if [ "$ROLE" = "viewer" ]; then
        print_status "PASS" "Admin role escalation blocked - role is viewer"
    else
        print_status "FAIL" "Admin role escalation NOT blocked - role is $ROLE"
    fi

    if [ "$IS_SUPERUSER" = "false" ]; then
        print_status "PASS" "Superuser flag is false"
    else
        print_status "FAIL" "Superuser flag is $IS_SUPERUSER (should be false)"
    fi
else
    print_status "FAIL" "Registration failed with HTTP $HTTP_CODE"
    echo "Response: $REGISTER_BODY"
fi
echo ""

# Step 3: Attempt analyst role escalation
print_status "INFO" "Step 3: Attempting to register with role=analyst"
REGISTER_ANALYST_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/auth/register" \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "attacker-analyst-'"$(date +%s)"'@test.com",
    "password": "Attack123!",
    "role": "analyst"
  }')

HTTP_CODE=$(echo "$REGISTER_ANALYST_RESPONSE" | tail -n 1)
REGISTER_BODY=$(echo "$REGISTER_ANALYST_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "201" ] || [ "$HTTP_CODE" = "200" ]; then
    ROLE=$(get_json_field "$REGISTER_BODY" "role")

    if [ "$ROLE" = "viewer" ]; then
        print_status "PASS" "Analyst role escalation blocked - role is viewer"
    else
        print_status "FAIL" "Analyst role escalation NOT blocked - role is $ROLE"
    fi
else
    print_status "FAIL" "Registration failed with HTTP $HTTP_CODE"
    echo "Response: $REGISTER_BODY"
fi
echo ""

# Step 4: Attempt multiple privilege escalation flags
print_status "INFO" "Step 4: Attempting to register with role=admin, is_superuser=true, is_verified=true"
ATTACKER_EMAIL="attacker-superuser-$(date +%s)@test.com"
REGISTER_SUPER_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/auth/register" \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "'"$ATTACKER_EMAIL"'",
    "password": "Attack123!",
    "role": "admin",
    "is_superuser": true,
    "is_verified": true
  }')

HTTP_CODE=$(echo "$REGISTER_SUPER_RESPONSE" | tail -n 1)
REGISTER_BODY=$(echo "$REGISTER_SUPER_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "201" ] || [ "$HTTP_CODE" = "200" ]; then
    ROLE=$(get_json_field "$REGISTER_BODY" "role")
    IS_SUPERUSER=$(get_json_field "$REGISTER_BODY" "is_superuser")
    IS_VERIFIED=$(get_json_field "$REGISTER_BODY" "is_verified")

    if [ "$ROLE" = "viewer" ]; then
        print_status "PASS" "Role escalation blocked - role is viewer"
    else
        print_status "FAIL" "Role escalation NOT blocked - role is $ROLE"
    fi

    if [ "$IS_SUPERUSER" = "false" ]; then
        print_status "PASS" "Superuser flag escalation blocked"
    else
        print_status "FAIL" "Superuser flag escalation NOT blocked - is_superuser is $IS_SUPERUSER"
    fi

    if [ "$IS_VERIFIED" = "false" ]; then
        print_status "PASS" "Email verification flag escalation blocked"
    else
        print_status "FAIL" "Email verification flag escalation NOT blocked - is_verified is $IS_VERIFIED"
    fi
else
    print_status "FAIL" "Registration failed with HTTP $HTTP_CODE"
    echo "Response: $REGISTER_BODY"
fi
echo ""

# Step 5: Login with attacker account
print_status "INFO" "Step 5: Logging in with attacker account"
LOGIN_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/auth/login" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d "username=$ATTACKER_EMAIL&password=Attack123!")

HTTP_CODE=$(echo "$LOGIN_RESPONSE" | tail -n 1)
LOGIN_BODY=$(echo "$LOGIN_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    ACCESS_TOKEN=$(get_json_field "$LOGIN_BODY" "access_token")

    if [ -n "$ACCESS_TOKEN" ] && [ "$ACCESS_TOKEN" != "null" ]; then
        print_status "PASS" "Login successful - access token received"
    else
        print_status "FAIL" "Login successful but no access token received"
        echo "Response: $LOGIN_BODY"
    fi
else
    print_status "FAIL" "Login failed with HTTP $HTTP_CODE"
    echo "Response: $LOGIN_BODY"
fi
echo ""

# Step 6: Verify user profile shows VIEWER role
if [ -n "$ACCESS_TOKEN" ] && [ "$ACCESS_TOKEN" != "null" ]; then
    print_status "INFO" "Step 6: Verifying user profile shows VIEWER role"
    PROFILE_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/users/me" \
      -H "Authorization: Bearer $ACCESS_TOKEN")

    HTTP_CODE=$(echo "$PROFILE_RESPONSE" | tail -n 1)
    PROFILE_BODY=$(echo "$PROFILE_RESPONSE" | head -n -1)

    if [ "$HTTP_CODE" = "200" ]; then
        ROLE=$(get_json_field "$PROFILE_BODY" "role")

        if [ "$ROLE" = "viewer" ]; then
            print_status "PASS" "User profile confirms VIEWER role"
        else
            print_status "FAIL" "User profile shows role=$ROLE (expected viewer)"
        fi
    else
        print_status "FAIL" "Failed to fetch user profile (HTTP $HTTP_CODE)"
        echo "Response: $PROFILE_BODY"
    fi
    echo ""

    # Step 7: Attempt to access admin endpoint
    print_status "INFO" "Step 7: Attempting to access admin endpoint (should be denied)"
    ADMIN_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/users" \
      -H "Authorization: Bearer $ACCESS_TOKEN")

    HTTP_CODE=$(echo "$ADMIN_RESPONSE" | tail -n 1)
    ADMIN_BODY=$(echo "$ADMIN_RESPONSE" | head -n -1)

    if [ "$HTTP_CODE" = "403" ]; then
        print_status "PASS" "Admin endpoint access denied (HTTP 403)"
    elif [ "$HTTP_CODE" = "401" ]; then
        print_status "PASS" "Admin endpoint access denied (HTTP 401)"
    elif [ "$HTTP_CODE" = "404" ]; then
        print_status "WARN" "Admin endpoint not found (HTTP 404) - cannot verify access control"
    else
        print_status "FAIL" "Admin endpoint returned HTTP $HTTP_CODE (expected 403)"
        echo "Response: $ADMIN_BODY"
    fi
    echo ""
else
    print_status "WARN" "Skipping steps 6-7 - no access token available"
    echo ""
fi

# Summary
echo "========================================="
echo "TEST SUMMARY"
echo "========================================="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
    echo ""
    echo "The role escalation vulnerability has been successfully fixed!"
    echo "All registration attempts with escalated privileges were blocked."
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo ""
    echo "The role escalation vulnerability fix may not be working correctly."
    echo "Please review the failed tests above and check the server logs."
    exit 1
fi
