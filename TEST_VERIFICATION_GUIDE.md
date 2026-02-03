# Backend Test Verification Guide

## Overview

This guide documents how to run the full backend test suite to verify that the role escalation security fix does not introduce any regressions.

## Environment Requirements

The tests require a Python environment with all dependencies installed. This can be achieved through:

1. **Virtual Environment** (Recommended for local development)
2. **Docker** (For containerized testing)
3. **CI/CD Pipeline** (Automated testing)

## Option 1: Virtual Environment

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Set required environment variables
export USE_SQLITE="true"
export SQLITE_URL="sqlite+aiosqlite:///:memory:"
export SECRET_KEY="test-secret-key-for-local-testing"
export OPENAI_API_KEY="test"
export OPENROUTER_API_KEY="test"
export TELEGRAM_API_ID="123"
export TELEGRAM_API_HASH="test"
export TELEGRAM_PHONE="+1000"
export SCHEDULER_ENABLED="false"
export API_USAGE_TRACKING_ENABLED="false"

# Run full test suite with verbose output
pytest tests/ -v --tb=short

# Or run with even more detail
pytest tests/ -v --tb=long -s
```

## Option 2: Docker

```bash
# Build the backend image
docker build -t osfeed-backend:test ./backend

# Run tests in container
docker run --rm \
  -e USE_SQLITE="true" \
  -e SQLITE_URL="sqlite+aiosqlite:///:memory:" \
  -e SECRET_KEY="test-secret-key" \
  -e OPENAI_API_KEY="test" \
  -e OPENROUTER_API_KEY="test" \
  -e TELEGRAM_API_ID="123" \
  -e TELEGRAM_API_HASH="test" \
  -e TELEGRAM_PHONE="+1000" \
  -e SCHEDULER_ENABLED="false" \
  -e API_USAGE_TRACKING_ENABLED="false" \
  osfeed-backend:test \
  pytest tests/ -v --tb=short
```

## Option 3: CI/CD Pipeline

The tests are automatically run in the CI/CD pipeline defined in `.github/workflows/ci.yml`. Simply push your changes and the pipeline will execute all tests.

## Expected Results

### All Tests Should Pass

The test suite includes:

1. **Authentication Tests** (`test_auth_registration.py`)
   - User registration flow
   - Password validation
   - Email verification
   - Login functionality

2. **Role Escalation Security Tests** (`test_auth_role_escalation.py`)
   - ✅ Default role assignment (VIEWER)
   - ✅ Admin role escalation prevention
   - ✅ Analyst role escalation prevention
   - ✅ Superuser flag prevention
   - ✅ is_verified flag prevention
   - ✅ Multiple privilege escalation attempts
   - ✅ Existing admin users unaffected

3. **Other Backend Tests**
   - All existing functionality tests
   - No regressions from the security fix

### Test Output Should Show

```
================================ test session starts ================================
collected XX items

tests/test_auth_registration.py::test_register_user PASSED                   [ XX%]
tests/test_auth_registration.py::test_login_user PASSED                      [ XX%]
...

tests/test_auth_role_escalation.py::test_register_default_role_is_viewer PASSED
tests/test_auth_role_escalation.py::test_register_with_admin_role_ignored PASSED
tests/test_auth_role_escalation.py::test_register_with_analyst_role_ignored PASSED
tests/test_auth_role_escalation.py::test_existing_admin_users_unaffected PASSED
tests/test_auth_role_escalation.py::test_register_with_superuser_flag_ignored PASSED
tests/test_auth_role_escalation.py::test_register_with_is_verified_flag_ignored PASSED
tests/test_auth_role_escalation.py::test_register_with_multiple_privilege_escalation_attempts PASSED

...

================================ XX passed in X.XXs =================================
```

## Troubleshooting

### Database Errors

If you encounter database errors, ensure:
- `USE_SQLITE="true"` is set for tests
- `SQLITE_URL="sqlite+aiosqlite:///:memory:"` uses in-memory database
- Or clear any test database files if using file-based sqlite

### Import Errors

If you see import errors:
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Verify virtual environment is activated
- Check that you're running from the backend directory

### Environment Variable Errors

If you see missing environment variable errors:
- Set all required environment variables as shown above
- Or create a `.env.test` file with test values

## Security Verification Checklist

After running the tests, verify:

- [ ] All tests pass (no failures or errors)
- [ ] No warnings about role field in UserCreate schema
- [ ] Role escalation tests all pass
- [ ] Existing authentication tests still pass
- [ ] No regressions in other backend functionality

## Next Steps

After successful test verification:

1. Proceed to **Subtask 4-2**: Manual verification of exploit attempt via curl
2. Verify the actual exploit attempt fails in a running environment
3. Complete QA sign-off for the security fix

## Notes

- Tests use in-memory SQLite for speed and isolation
- Production uses PostgreSQL, but tests verify business logic
- All security tests verify both API response AND database state
- Defense-in-depth: Tests verify both schema-level and UserManager-level protection
