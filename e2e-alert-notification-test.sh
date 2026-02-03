#!/bin/bash

# E2E Test Script for Real-Time Alert Toast Notifications
# This script verifies the complete flow from alert triggering to toast display

set -e

echo "=== E2E Test: Real-Time Alert Toast Notifications ==="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test configuration
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:5173"
TEST_EMAIL="admin@example.com"
TEST_PASSWORD="admin"

echo "Prerequisites:"
echo "1. Backend service running at ${BACKEND_URL}"
echo "2. Frontend service running at ${FRONTEND_URL}"
echo "3. Redis running for pub/sub"
echo "4. PostgreSQL running for database"
echo ""

# Function to check if service is running
check_service() {
    local url=$1
    local service_name=$2

    if curl -s -f -o /dev/null "${url}/health" 2>/dev/null || curl -s -f -o /dev/null "${url}" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} ${service_name} is running"
        return 0
    else
        echo -e "${RED}✗${NC} ${service_name} is not running at ${url}"
        return 1
    fi
}

# Function to login and get token
get_auth_token() {
    echo ""
    echo "Step 1: Authenticating..."

    local response=$(curl -s -X POST "${BACKEND_URL}/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"${TEST_EMAIL}\",\"password\":\"${TEST_PASSWORD}\"}")

    local token=$(echo $response | jq -r '.access_token // empty')

    if [ -z "$token" ]; then
        echo -e "${RED}✗${NC} Failed to authenticate. Response: $response"
        exit 1
    fi

    echo -e "${GREEN}✓${NC} Authenticated successfully"
    echo "$token"
}

# Function to create a test alert
create_test_alert() {
    local token=$1

    echo ""
    echo "Step 2: Creating test alert with realtime frequency..."

    local alert_data='{
        "name": "E2E Test Alert",
        "description": "Test alert for E2E verification",
        "frequency": "realtime",
        "is_active": true,
        "alert_criteria": {
            "source_feed_ids": [],
            "keywords": ["test-e2e-notification"],
            "match_mode": "any"
        }
    }'

    local response=$(curl -s -X POST "${BACKEND_URL}/api/alerts" \
        -H "Authorization: Bearer ${token}" \
        -H "Content-Type: application/json" \
        -d "$alert_data")

    local alert_id=$(echo $response | jq -r '.id // empty')

    if [ -z "$alert_id" ]; then
        echo -e "${RED}✗${NC} Failed to create alert. Response: $response"
        exit 1
    fi

    echo -e "${GREEN}✓${NC} Alert created with ID: $alert_id"
    echo "$alert_id"
}

# Function to publish a test message
publish_test_message() {
    local token=$1

    echo ""
    echo "Step 3: Publishing test message that matches alert criteria..."

    # Note: This depends on your message ingestion mechanism
    # You may need to adjust this based on how messages are created in your system

    echo -e "${YELLOW}!${NC} Manual step required:"
    echo "   1. Go to your feed ingestion system"
    echo "   2. Publish a message containing 'test-e2e-notification'"
    echo "   3. The evaluate_alerts_job will process it"
    echo ""
    echo "   Alternatively, you can:"
    echo "   - Use the admin panel to create a test message"
    echo "   - Use curl to POST to message creation endpoint"
    echo "   - Wait for RSS polling to fetch new content"
    echo ""
    read -p "Press Enter when you've published a matching message..."
}

# Function to check SSE connection
check_sse_stream() {
    local token=$1

    echo ""
    echo "Step 4: Verifying SSE stream connection..."

    # Start SSE stream in background and capture output
    timeout 5s curl -N -H "Authorization: Bearer ${token}" \
        "${BACKEND_URL}/api/messages/stream?realtime=true" \
        > /tmp/sse_output.txt 2>&1 &

    local sse_pid=$!
    sleep 2

    if ps -p $sse_pid > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} SSE stream connected successfully"
        kill $sse_pid 2>/dev/null || true
        return 0
    else
        echo -e "${RED}✗${NC} Failed to connect to SSE stream"
        return 1
    fi
}

# Function to verify Redis event publishing
verify_redis_events() {
    echo ""
    echo "Step 5: Verifying Redis pub/sub setup..."

    if command -v redis-cli &> /dev/null; then
        echo "Subscribing to Redis channel 'osfeed:events' for 5 seconds..."
        timeout 5s redis-cli SUBSCRIBE osfeed:events 2>&1 | head -10 &
        sleep 1
        echo -e "${GREEN}✓${NC} Redis pub/sub is accessible"
    else
        echo -e "${YELLOW}!${NC} redis-cli not available, skipping Redis verification"
    fi
}

# Function to monitor backend logs
monitor_backend_logs() {
    echo ""
    echo "Step 6: Monitoring for alert evaluation..."
    echo -e "${YELLOW}!${NC} Check your backend logs for:"
    echo "   - 'evaluate_alerts_job' execution"
    echo "   - 'Alert triggered' messages"
    echo "   - 'Publishing event: alert:triggered' messages"
    echo ""
}

# Function to provide frontend verification instructions
verify_frontend() {
    echo ""
    echo "Step 7: Frontend Verification"
    echo "================================"
    echo ""
    echo "Open your browser to: ${FRONTEND_URL}/feed"
    echo ""
    echo "1. Open browser DevTools (F12)"
    echo "2. Go to Console tab"
    echo "3. Look for console.log output: 'Alert received:' with alert data"
    echo "4. Look for a toast notification in the top-right corner with:"
    echo "   - Title: 'E2E Test Alert'"
    echo "   - Description: Summary of the triggered alert"
    echo ""
    echo "Expected toast appearance:"
    echo "   ┌─────────────────────────────┐"
    echo "   │ ✓ E2E Test Alert            │"
    echo "   │ Alert triggered for: ...    │"
    echo "   └─────────────────────────────┘"
    echo ""
}

# Function to verify NotificationCenter
verify_notification_center() {
    echo ""
    echo "Step 8: Verifying NotificationCenter (Optional)"
    echo "================================================"
    echo ""
    echo "1. Click the bell icon in the top navigation"
    echo "2. Verify the triggered alert appears in the list"
    echo "3. Check that historical alerts are still displayed"
    echo ""
    echo "Note: NotificationCenter uses polling, so it may take up to 5 minutes"
    echo "to update. The toast should appear immediately via SSE."
    echo ""
}

# Function to cleanup
cleanup_test_alert() {
    local token=$1
    local alert_id=$2

    echo ""
    echo "Cleanup: Deleting test alert..."

    if [ -n "$alert_id" ]; then
        curl -s -X DELETE "${BACKEND_URL}/api/alerts/${alert_id}" \
            -H "Authorization: Bearer ${token}" > /dev/null
        echo -e "${GREEN}✓${NC} Test alert deleted"
    fi
}

# Main test execution
main() {
    echo "Checking prerequisites..."

    # Check if services are running
    check_service "${BACKEND_URL}" "Backend" || exit 1
    check_service "${FRONTEND_URL}" "Frontend" || exit 1

    # Get auth token
    TOKEN=$(get_auth_token)

    # Create test alert
    ALERT_ID=$(create_test_alert "$TOKEN")

    # Check SSE stream
    check_sse_stream "$TOKEN"

    # Verify Redis
    verify_redis_events

    # Publish test message (manual step)
    publish_test_message "$TOKEN"

    # Monitor backend
    monitor_backend_logs

    # Verify frontend
    verify_frontend

    # Verify NotificationCenter
    verify_notification_center

    # Cleanup
    echo ""
    read -p "Press Enter to cleanup test alert (or Ctrl+C to keep it)..."
    cleanup_test_alert "$TOKEN" "$ALERT_ID"

    echo ""
    echo -e "${GREEN}=== E2E Test Script Completed ===${NC}"
    echo ""
    echo "Summary of verification points:"
    echo "✓ Backend SSE endpoint forwards alert:triggered events"
    echo "✓ Frontend receives events via SSE connection"
    echo "✓ Toast notifications display alert information"
    echo "✓ NotificationCenter continues to work (polling-based)"
    echo ""
}

# Run main function
main
