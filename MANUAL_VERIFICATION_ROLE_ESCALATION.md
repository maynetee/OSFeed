# Manual Verification: Role Escalation Attack Prevention

## Overview

This document provides step-by-step instructions for manually verifying that the role escalation vulnerability has been fixed. The fix enforces that all new user registrations receive the VIEWER role, regardless of what role is specified in the registration request.

## Security Fix Implementation

The fix is implemented in `backend/app/auth/users.py` in the `UserManager.create()` method (lines 91-126):

```python
async def create(self, user_create, safe: bool = False, request: Optional[Request] = None):
    """
    Override create to enforce VIEWER role for all new users.

    This prevents privilege escalation by forcing all newly registered
    users to have the VIEWER role, regardless of what role was requested.
    """
    # Force role to VIEWER to prevent privilege escalation
    user_dict = user_create.dict() if hasattr(user_create, 'dict') else user_create.model_dump()
    user_dict['role'] = UserRole.VIEWER

    # Log if a different role was attempted
    if hasattr(user_create, 'role') and user_create.role != UserRole.VIEWER:
        logger.warning(
            f"User registration attempted with role {user_create.role}, "
            f"enforcing VIEWER role instead"
        )

    # Create new user_create object with enforced role
    user_create_safe = type(user_create)(**user_dict)

    # Call parent create with enforced role
    return await super().create(user_create_safe, safe=safe, request=request)
```

**Note:** While the `role` field still exists in the `UserCreate` schema (`backend/app/schemas/user.py`, line 22), the server-side enforcement in `UserManager.create()` ensures that any role value is overridden to `VIEWER`. This provides defense-in-depth security.

## Prerequisites

Before running the manual verification:

1. **Backend server must be running** with database configured
2. **curl** command-line tool installed
3. **jq** (optional, for JSON formatting)

## Setup: Start the Backend Server

### Option 1: Using Docker Compose (Recommended)

```bash
# From project root
docker-compose up backend postgres redis

# Wait for backend to be ready (watch for "Application startup complete")
```

### Option 2: Local Python Environment

```bash
# Navigate to backend directory
cd backend

# Set environment variables
export USE_SQLITE="false"
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/osfeed"
export SECRET_KEY="test-secret-key-for-manual-verification"
export OPENAI_API_KEY="test"
export OPENROUTER_API_KEY="test"
export TELEGRAM_API_ID="123"
export TELEGRAM_API_HASH="test"
export TELEGRAM_PHONE="+1000"
export SCHEDULER_ENABLED="false"
export API_USAGE_TRACKING_ENABLED="false"

# Start PostgreSQL and Redis (if not already running)
docker-compose -f ../docker-compose.infra.yml up -d

# Run migrations
alembic upgrade head

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Verification Steps

### Step 1: Verify Server is Running

```bash
curl http://localhost:8000/api/health
```

**Expected Response:**
```json
{"status": "ok"}
```

### Step 2: Attempt Role Escalation Attack - Admin Role

This is the primary attack vector being tested.

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "attacker-admin@test.com",
    "password": "Attack123!",
    "role": "admin"
  }'
```

**Expected Response:**
```json
{
  "id": "<uuid>",
  "email": "attacker-admin@test.com",
  "is_active": true,
  "is_superuser": false,
  "is_verified": false,
  "role": "viewer",
  "full_name": null,
  "preferred_language": "en",
  "consent_given_at": null,
  "last_login_at": null,
  "created_at": "<timestamp>"
}
```

**✅ PASS CRITERIA:** `"role": "viewer"` (NOT "admin")

### Step 3: Attempt Role Escalation Attack - Analyst Role

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "attacker-analyst@test.com",
    "password": "Attack123!",
    "role": "analyst"
  }'
```

**Expected Response:**
```json
{
  "id": "<uuid>",
  "email": "attacker-analyst@test.com",
  "is_active": true,
  "is_superuser": false,
  "is_verified": false,
  "role": "viewer",
  ...
}
```

**✅ PASS CRITERIA:** `"role": "viewer"` (NOT "analyst")

### Step 4: Attempt Superuser Flag Escalation

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "attacker-superuser@test.com",
    "password": "Attack123!",
    "role": "admin",
    "is_superuser": true,
    "is_verified": true
  }'
```

**Expected Response:**
```json
{
  "id": "<uuid>",
  "email": "attacker-superuser@test.com",
  "is_active": true,
  "is_superuser": false,
  "is_verified": false,
  "role": "viewer",
  ...
}
```

**✅ PASS CRITERIA:**
- `"role": "viewer"`
- `"is_superuser": false`
- `"is_verified": false`

### Step 5: Login with the Attacker Account

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=attacker-admin@test.com&password=Attack123!'
```

**Expected Response:**
```json
{
  "access_token": "<jwt_token>",
  "token_type": "bearer"
}
```

**Save the access token for the next step:**
```bash
TOKEN="<jwt_token_from_response>"
```

### Step 6: Verify User Profile Shows VIEWER Role

```bash
curl http://localhost:8000/api/users/me \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "id": "<uuid>",
  "email": "attacker-admin@test.com",
  "role": "viewer",
  "is_superuser": false,
  ...
}
```

**✅ PASS CRITERIA:** `"role": "viewer"`

### Step 7: Attempt to Access Admin-Only Endpoint

Test accessing an admin-privileged endpoint (e.g., listing all users, which typically requires admin role):

```bash
curl http://localhost:8000/api/users \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "detail": "Forbidden"
}
```

**Expected HTTP Status:** `403 Forbidden`

**✅ PASS CRITERIA:**
- HTTP 403 status code
- Access denied message

**Note:** If the endpoint doesn't exist or returns 404, try another admin endpoint. The key is that VIEWER role should not have access to admin operations.

### Step 8: Check Server Logs for Security Warning

Check the backend server logs for the security warning message:

```bash
# If using Docker:
docker-compose logs backend | grep "User registration attempted with role"

# If running locally:
# Check your terminal output where uvicorn is running
```

**Expected Log Entry:**
```
WARNING: User registration attempted with role admin, enforcing VIEWER role instead
```

**✅ PASS CRITERIA:** Log message confirms the role enforcement

## Verification Summary Checklist

After completing all steps, verify:

- [x] Step 1: Server health check passes
- [x] Step 2: Admin role escalation blocked (role=viewer returned)
- [x] Step 3: Analyst role escalation blocked (role=viewer returned)
- [x] Step 4: Superuser flag escalation blocked (role=viewer, is_superuser=false)
- [x] Step 5: Login with attacker account successful
- [x] Step 6: User profile confirms VIEWER role
- [x] Step 7: Admin endpoint access denied (403 Forbidden)
- [x] Step 8: Server logs show security warning

## Expected Outcome

**✅ VULNERABILITY FIXED:** All new user registrations are forced to VIEWER role, regardless of the role specified in the request. Any attempt to escalate privileges during registration is blocked and logged.

## Security Analysis

### Defense-in-Depth Layers

1. **Server-Side Enforcement (PRIMARY):** `UserManager.create()` method explicitly forces `role=VIEWER` for all new users
2. **Logging:** Attempted privilege escalation is logged with WARNING level
3. **FastAPI-Users Safe Mode:** The `safe=True` parameter protects `is_superuser`, `is_verified`, and `is_active` fields

### Remaining Risk

**Schema-Level:** The `role` field still exists in the `UserCreate` schema (`backend/app/schemas/user.py`). While this doesn't pose a security risk due to server-side enforcement, it could be misleading to API consumers.

**Recommendation:** Consider removing the `role` field from `UserCreate` schema entirely for defense-in-depth and to prevent confusion. This was the intent of subtask-1-1 but appears not to have been implemented.

## Cleanup

After verification, you may want to remove the test accounts:

```bash
# Connect to database and run:
DELETE FROM users WHERE email LIKE 'attacker-%@test.com';
```

## Troubleshooting

### Server Won't Start

- Check that PostgreSQL and Redis are running
- Verify all environment variables are set
- Check for port 8000 already in use: `lsof -i :8000`

### Registration Fails

- Verify password meets requirements (8+ chars, upper, lower, digit, special char)
- Check that email is unique
- Review server logs for detailed error messages

### Can't Access Admin Endpoint

- Verify you're using a valid JWT token
- Check token hasn't expired (default lifetime: configured in settings)
- Ensure the Authorization header is formatted correctly: `Bearer <token>`

## References

- Vulnerability Spec: `.auto-claude/specs/016-fix-role-escalation-vulnerability-in-user-registra/spec.md`
- Implementation Plan: `.auto-claude/specs/016-fix-role-escalation-vulnerability-in-user-registra/implementation_plan.json`
- User Manager Implementation: `backend/app/auth/users.py`
- User Schemas: `backend/app/schemas/user.py`
- Security Tests: `backend/tests/test_auth_role_escalation.py`
