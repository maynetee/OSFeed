# E2E Verification: Real-Time Alert Toast Notifications

## Overview

This document provides step-by-step instructions for verifying the complete real-time alert notification flow from backend event publishing to frontend toast display.

## Architecture Flow

```
Alert Evaluation → Redis Pub/Sub → SSE Stream → Frontend → Toast Display
     (Backend)      (osfeed:events)  (messages.py)  (useMessageStream)  (Sonner)
```

## Implementation Changes

### Backend (subtask-1-1)
- **File**: `backend/app/api/messages.py`
- **Change**: Added handler for `alert:triggered` events in SSE stream
- **Lines**: ~240-247
- **Pattern**: Mirrors existing `message:translated` handler

### Frontend - Toast Library (subtask-2-1, 2-2)
- **File**: `frontend/package.json`
- **Change**: Added `sonner@^1.3.1` dependency
- **File**: `frontend/src/components/layout/app-shell.tsx`
- **Change**: Added `<Toaster position='top-right' richColors />`

### Frontend - Event Handler (subtask-3-1, 3-2)
- **File**: `frontend/src/hooks/use-message-stream.ts`
- **Change**: Added `onAlert` callback to interface and event handling logic
- **Lines**: ~87-92
- **File**: `frontend/src/components/layout/app-shell.tsx`
- **Change**: Added `useMessageStream` with `onAlert` callback to display toasts

## Prerequisites

Before starting the E2E test, ensure:

1. ✅ **Backend service** is running at `http://localhost:8000`
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. ✅ **Frontend service** is running at `http://localhost:5173`
   ```bash
   cd frontend
   npm run dev
   ```

3. ✅ **Redis** is running and accessible
   ```bash
   redis-cli ping  # Should return "PONG"
   ```

4. ✅ **PostgreSQL** is running with the OSFeed database

5. ✅ **Dependencies** are installed
   ```bash
   cd frontend && npm install  # Installs sonner
   ```

## E2E Test Steps

### Step 1: Verify Backend SSE Endpoint

**Objective**: Confirm SSE endpoint accepts connections and forwards events

**Method**:
```bash
# Get auth token first
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin"}' \
  | jq -r '.access_token')

# Connect to SSE stream
curl -N -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/messages/stream?realtime=true"
```

**Expected**:
- Connection established (no immediate errors)
- Periodic heartbeat events (`:ping\n\n`)
- No error messages in backend logs

**Verification**:
- [ ] SSE connection successful
- [ ] No errors in terminal or backend logs

---

### Step 2: Create Test Alert

**Objective**: Create an active alert with realtime frequency

**Method** (Option A - UI):
1. Navigate to `http://localhost:5173/alerts`
2. Click "Create Alert"
3. Fill in:
   - **Name**: "E2E Test Alert"
   - **Description**: "Testing real-time notifications"
   - **Frequency**: "Realtime"
   - **Status**: Active (checked)
   - **Keywords**: "test-notification-keyword"
4. Click "Create"

**Method** (Option B - API):
```bash
curl -X POST http://localhost:8000/api/alerts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "E2E Test Alert",
    "description": "Testing real-time notifications",
    "frequency": "realtime",
    "is_active": true,
    "alert_criteria": {
      "keywords": ["test-notification-keyword"],
      "match_mode": "any"
    }
  }'
```

**Expected**:
- Alert created successfully
- Returns alert object with `id` field

**Verification**:
- [ ] Alert appears in alerts list
- [ ] Alert status is "Active"
- [ ] Alert frequency is "Realtime"

---

### Step 3: Monitor Redis Pub/Sub (Optional)

**Objective**: Verify events are published to Redis channel

**Method**:
```bash
# In a separate terminal
redis-cli SUBSCRIBE osfeed:events
```

**Expected**:
- Subscribed to channel successfully
- Will see `alert:triggered` events when alerts fire

**Verification**:
- [ ] Redis subscription active
- [ ] Can see events being published

---

### Step 4: Prepare Frontend for Monitoring

**Objective**: Set up browser to observe toast notifications

**Method**:
1. Open browser to `http://localhost:5173/feed`
2. Open DevTools (F12)
3. Go to Console tab
4. Clear console for clean output
5. Ensure you're logged in

**Expected**:
- App loads without errors
- SSE connection established (check Network tab → EventStream)
- No console errors

**Verification**:
- [ ] Frontend app loaded successfully
- [ ] No errors in console
- [ ] SSE connection visible in Network tab

---

### Step 5: Trigger the Alert

**Objective**: Create/update a message that matches alert criteria

**Method** (Option A - Create Test Message):

If your system has a manual message creation endpoint:
```bash
curl -X POST http://localhost:8000/api/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test message with test-notification-keyword",
    "content": "This message should trigger our E2E test alert",
    "source_feed_id": 1
  }'
```

**Method** (Option B - RSS Feed):
1. Add an RSS feed that contains the keyword
2. Wait for RSS polling job to run
3. Or trigger manual RSS fetch

**Method** (Option C - Database Insert):
```sql
INSERT INTO messages (title, content, source_feed_id, published_at, created_at)
VALUES (
  'Test message with test-notification-keyword',
  'Content for E2E testing',
  1,
  NOW(),
  NOW()
);
```

Then trigger alert evaluation:
```bash
# Trigger evaluation job manually if needed
curl -X POST http://localhost:8000/api/admin/jobs/evaluate_alerts \
  -H "Authorization: Bearer $TOKEN"
```

**Expected**:
- Message created/ingested successfully
- Alert evaluation job processes the message

**Verification**:
- [ ] Message created
- [ ] Message contains alert keyword

---

### Step 6: Verify Backend Processing

**Objective**: Confirm backend detects match and publishes event

**Method**:
Check backend logs for:

```
INFO: evaluate_alerts_job: Evaluating alerts...
INFO: Alert triggered: E2E Test Alert
INFO: Publishing event: alert:triggered
```

If monitoring Redis (from Step 3):
```
1) "message"
2) "osfeed:events"
3) "{\"type\":\"alert:triggered\",\"data\":{\"alert_id\":123,\"alert_name\":\"E2E Test Alert\",\"summary\":\"...\"}}"
```

**Expected**:
- Backend logs show alert evaluation
- Alert is triggered
- Event is published to Redis

**Verification**:
- [ ] Backend logs show alert triggered
- [ ] Redis receives event (if monitoring)
- [ ] No errors in backend logs

---

### Step 7: Verify SSE Forwarding

**Objective**: Confirm SSE endpoint forwards alert event to frontend

**Method**:
If you kept the SSE curl connection from Step 1, you should see:

```
event: alert:triggered
data: {"alert_id":123,"alert_name":"E2E Test Alert","summary":"..."}

```

**Expected**:
- SSE stream receives and forwards the event
- Event type is `alert:triggered`
- Event data contains alert details

**Verification**:
- [ ] SSE stream forwards alert event
- [ ] Event format is correct JSON

---

### Step 8: Verify Frontend Event Reception

**Objective**: Confirm frontend receives and processes the alert event

**Method**:
1. Check browser console (DevTools)
2. Look for log output from `use-message-stream.ts`:
   ```
   Alert received: {alert_id: 123, alert_name: "E2E Test Alert", summary: "..."}
   ```

**Expected**:
- Console shows "Alert received:" log with event data
- No JavaScript errors

**Verification**:
- [ ] Console shows alert received log
- [ ] Alert data structure is correct
- [ ] No errors in console

---

### Step 9: Verify Toast Notification Display

**Objective**: Confirm toast notification appears in the UI

**Method**:
1. Watch the top-right corner of the browser
2. A toast notification should appear:

```
┌─────────────────────────────────────┐
│ ✓ E2E Test Alert                    │
│ Alert triggered for: [message title]│
└─────────────────────────────────────┘
```

The toast should:
- Appear in the top-right corner
- Have a green success style (from `toast.success`)
- Show alert name as title
- Show summary as description
- Auto-dismiss after a few seconds
- Be accessible (keyboard navigable)

**Expected**:
- Toast appears immediately after event is received
- Toast displays correct alert information
- Toast auto-dismisses
- Animation is smooth

**Verification**:
- [ ] Toast notification appears
- [ ] Toast shows alert name correctly
- [ ] Toast shows summary/description
- [ ] Toast has success styling (green)
- [ ] Toast auto-dismisses

---

### Step 10: Verify NotificationCenter (Optional)

**Objective**: Confirm existing notification system still works

**Method**:
1. Click the bell icon (🔔) in top navigation
2. Wait up to 5 minutes for polling interval
3. Check that the triggered alert appears in the list

**Expected**:
- NotificationCenter still functions
- Shows historical alerts (polling-based)
- New alert appears after polling interval

**Verification**:
- [ ] NotificationCenter opens successfully
- [ ] Shows list of notifications
- [ ] New alert appears (may take time due to polling)

---

## Success Criteria

All of the following must be true for E2E test to pass:

- ✅ Backend SSE endpoint accepts connections
- ✅ Alert can be created with realtime frequency
- ✅ Matching messages trigger alert evaluation
- ✅ Backend publishes `alert:triggered` event to Redis
- ✅ SSE stream forwards event to connected clients
- ✅ Frontend receives event via `useMessageStream` hook
- ✅ Toast notification appears in browser UI
- ✅ Toast displays correct alert information
- ✅ No errors in backend or frontend logs
- ✅ Existing NotificationCenter still works

## Troubleshooting

### No Toast Appears

**Check**:
1. Browser console for errors
2. Network tab → EventStream connection active?
3. Console shows "Alert received:" log?
4. Backend logs show event published?

**Common Issues**:
- SSE connection dropped (check Network tab)
- Sonner not installed (`npm install` in frontend)
- `onAlert` callback not registered
- User not logged in

### SSE Connection Fails

**Check**:
1. Backend running and accessible?
2. Valid auth token?
3. CORS headers configured?

**Common Issues**:
- Backend not running
- Token expired
- Network proxy interfering

### Alert Not Triggered

**Check**:
1. Alert is active?
2. Message matches criteria?
3. Alert frequency is "realtime"?
4. Evaluation job ran?

**Common Issues**:
- Keyword mismatch (case-sensitive?)
- Alert not active
- Evaluation job not running

### Toast Appears But Wrong Data

**Check**:
1. Event payload structure
2. Frontend mapping in `onAlert` callback
3. Backend event publishing format

**Common Issues**:
- Field name mismatch (e.g., `alert_name` vs `name`)
- Missing fields in payload
- Type mismatch

## Performance Verification

### Latency Test

Measure time from alert trigger to toast display:

1. Note time when message is created
2. Note time when toast appears
3. Calculate difference

**Expected**: < 2 seconds for realtime alerts

### Resource Usage

**Check**:
1. Browser memory usage (DevTools → Memory)
2. SSE connection stability over time
3. No memory leaks from event listeners

**Expected**:
- Memory usage stable over time
- SSE connection remains open
- No accumulation of event listeners

## Cleanup

After testing, clean up test data:

1. **Delete test alert**:
   ```bash
   curl -X DELETE http://localhost:8000/api/alerts/{alert_id} \
     -H "Authorization: Bearer $TOKEN"
   ```

2. **Delete test messages** (if created):
   ```sql
   DELETE FROM messages WHERE title LIKE '%test-notification-keyword%';
   ```

3. **Close SSE connections**:
   - Stop curl command (Ctrl+C)
   - Refresh browser to reset connection

## Test Automation Opportunities

For future automation, consider:

1. **Playwright E2E test**: Automate browser interaction and toast verification
2. **Backend integration test**: Mock Redis and verify event publishing
3. **Frontend component test**: Test `useMessageStream` hook with mock SSE
4. **API test**: Test alert CRUD operations

## Additional Verification

### Code Review Checklist

- [ ] Backend forwards `alert:triggered` events (messages.py ~240-247)
- [ ] Frontend has `onAlert` callback in `useMessageStream` hook
- [ ] AppShell calls `useMessageStream` with `onAlert`
- [ ] Toaster component added to AppShell
- [ ] Sonner dependency in package.json
- [ ] No console.log debugging statements (except verification logs)
- [ ] Error handling in place
- [ ] TypeScript types correct

### Security Checklist

- [ ] SSE endpoint requires authentication
- [ ] Alert data doesn't leak sensitive information
- [ ] XSS protection for toast content
- [ ] CSRF protection on alert CRUD endpoints

### Accessibility Checklist

- [ ] Toast is announced by screen readers
- [ ] Toast can be dismissed with keyboard
- [ ] Toast has sufficient color contrast
- [ ] Toast doesn't block critical UI

## Conclusion

This E2E verification ensures the complete real-time alert notification flow works as expected, from backend event publishing through SSE to frontend toast display.

**Estimated Time**: 15-20 minutes for manual verification
**Automation Potential**: High (Playwright + API tests)
**Risk Level**: Low (extends existing infrastructure)
