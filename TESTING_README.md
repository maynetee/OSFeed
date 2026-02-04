# Manual Browser Testing - Cookie-Based Authentication

## Subtask 3-1: Integration Testing

This directory contains everything you need to perform manual browser testing of the cookie-based authentication implementation.

---

## Quick Start

### Option 1: Automated Service Startup (Recommended)

```bash
./start-services-for-testing.sh
```

This will:
- Start the backend on port 8000
- Start the frontend on port 5173
- Wait for both to be ready
- Keep running until you press Ctrl+C

To stop:
```bash
./stop-test-services.sh
```
Or press Ctrl+C

### Option 2: Manual Startup

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

---

## Testing Process

### Step 1: Pre-Test Verification (Optional but Recommended)

Before manual testing, verify the backend implementation:

```bash
./pre-test-verification.sh
```

This script will:
- ✓ Check if backend is running
- ✓ Verify login endpoint sets cookies
- ✓ Verify cookies have HttpOnly flag
- ✓ Verify tokens are NOT in JSON response
- ✓ Run backend unit tests

**If any checks fail, fix them before proceeding!**

### Step 2: Manual Browser Testing

Open the comprehensive testing guide:

```bash
cat MANUAL_TESTING_GUIDE.md
# or
open MANUAL_TESTING_GUIDE.md
```

The guide includes 5 test scenarios:

1. **Login Flow with Cookie Verification**
   - Login and verify cookies are set with correct attributes
   - Verify localStorage does NOT contain tokens

2. **Protected Page Access**
   - Verify authenticated requests work
   - Verify cookies are sent automatically

3. **Token Refresh Flow**
   - Delete access_token cookie manually
   - Verify automatic refresh works
   - Verify new cookies are set

4. **Logout Flow**
   - Logout and verify cookies are cleared
   - Verify cannot access protected pages

5. **Security Verification**
   - Verify `document.cookie` does NOT show tokens (httpOnly works)
   - Verify localStorage does NOT contain tokens
   - Verify network requests use cookies, not Authorization headers

---

## Test Checklist

Use this quick checklist during testing:

- [ ] Backend running on http://localhost:8000
- [ ] Frontend running on http://localhost:5173
- [ ] Pre-test verification passed (optional)
- [ ] Login sets access_token cookie with HttpOnly
- [ ] Login sets refresh_token cookie with HttpOnly
- [ ] Cookies have SameSite=Lax
- [ ] localStorage does NOT have tokens
- [ ] Protected pages accessible when authenticated
- [ ] Token refresh works automatically (tested by deleting access_token)
- [ ] Logout clears both cookies
- [ ] Cannot access protected pages after logout
- [ ] `document.cookie` does NOT show tokens
- [ ] Network tab shows Cookie header in requests
- [ ] Network tab does NOT show Authorization: Bearer header

---

## Important Security Checks

### ✓ HttpOnly Flag
- **What:** Prevents JavaScript from accessing cookies
- **How to verify:** Run `document.cookie` in browser console after login
- **Expected:** Tokens should NOT appear in output

### ✓ SameSite Attribute
- **What:** Prevents CSRF attacks
- **How to verify:** Inspect cookie in DevTools > Application > Cookies
- **Expected:** SameSite should be "Lax"

### ✓ Tokens Not in localStorage
- **What:** Ensures XSS can't exfiltrate tokens from localStorage
- **How to verify:** DevTools > Application > Local Storage
- **Expected:** `osfeed-auth` should only contain user info (no tokens)

### ✓ Automatic Cookie Transmission
- **What:** Cookies sent automatically with every request
- **How to verify:** DevTools > Network > Request Headers
- **Expected:** `Cookie: access_token=...` header present

---

## Common Issues

### Issue: Cookies not showing up

**Possible causes:**
1. Backend not setting cookies correctly
2. CORS configuration missing `credentials: true`
3. SameSite attribute too strict

**Debug:**
```bash
# Check login response headers
curl -i -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test@example.com","password":"password"}'

# Look for Set-Cookie headers
```

### Issue: CORS error with credentials

**Error:** "Access-Control-Allow-Credentials" header in response is ''

**Fix:** Backend CORS middleware must have:
```python
allow_credentials=True
```

### Issue: Tokens in localStorage

**Cause:** Frontend still using old code

**Fix:** Verify these files were updated:
- `frontend/src/stores/user-store.ts` - removed tokens field
- `frontend/src/lib/api/axios-instance.ts` - added withCredentials: true
- `frontend/src/features/auth/login-page.tsx` - not extracting tokens

### Issue: Refresh not working

**Debug steps:**
1. Open DevTools > Network tab
2. Make a request that requires auth
3. Look for:
   - 401 Unauthorized response
   - Automatic call to `/api/auth/refresh`
   - Retry of original request

**Common causes:**
- refresh_token cookie not being sent
- Backend not reading cookie correctly
- Response interceptor not configured correctly

---

## File Reference

### Implementation Files

**Backend:**
- `backend/app/config.py` - Cookie configuration settings
- `backend/app/api/auth.py` - Login, refresh, logout endpoints
- `backend/tests/test_auth_refresh.py` - Refresh flow tests
- `backend/tests/test_auth_logout.py` - Logout tests

**Frontend:**
- `frontend/src/stores/user-store.ts` - User state (tokens removed)
- `frontend/src/lib/api/axios-instance.ts` - HTTP client with withCredentials
- `frontend/src/lib/api/auth.ts` - Auth API calls
- `frontend/src/features/auth/login-page.tsx` - Login page

### Testing Files

- `MANUAL_TESTING_GUIDE.md` - Comprehensive test scenarios (main guide)
- `TESTING_README.md` - This file (overview and quick reference)
- `start-services-for-testing.sh` - Start both services
- `stop-test-services.sh` - Stop both services
- `pre-test-verification.sh` - Automated backend checks

---

## Success Criteria

All items must pass before marking subtask as complete:

**Configuration:**
- [x] Backend has cookie settings in config.py
- [x] Cookies have httpOnly=True, samesite='lax'
- [x] Frontend has withCredentials: true

**Functionality:**
- [ ] Login sets both cookies
- [ ] Protected pages work with cookies
- [ ] Refresh flow works automatically
- [ ] Logout clears cookies

**Security:**
- [ ] HttpOnly prevents JavaScript access
- [ ] localStorage does NOT have tokens
- [ ] Tokens only in cookies
- [ ] No Authorization: Bearer headers

**Tests:**
- [x] Backend unit tests pass
- [ ] Manual browser tests pass

---

## After Testing

### If All Tests Pass ✓

1. Update build progress:
   ```bash
   echo "Subtask-3-1 COMPLETED - All manual browser tests passed" >> \
     .auto-claude/specs/017-move-jwt-tokens-from-localstorage-to-secure-httpon/build-progress.txt
   ```

2. Commit the testing documentation:
   ```bash
   git add MANUAL_TESTING_GUIDE.md TESTING_README.md *.sh
   git commit -m "auto-claude: subtask-3-1 - Manual browser testing of complete auth flow

   - Created comprehensive manual testing guide
   - Added automated pre-test verification script
   - Added service startup/shutdown scripts
   - Verified cookie-based auth flow end-to-end
   - All security checks passed"
   ```

3. Update implementation_plan.json (mark subtask-3-1 as completed)

### If Tests Fail ✗

1. Document the failure in build-progress.txt
2. Debug and fix the issue
3. Re-run tests
4. Only mark complete when ALL tests pass

---

## Questions?

Review the implementation plan:
```bash
cat .auto-claude/specs/017-move-jwt-tokens-from-localstorage-to-secure-httpon/implementation_plan.json
```

Check build progress:
```bash
cat .auto-claude/specs/017-move-jwt-tokens-from-localstorage-to-secure-httpon/build-progress.txt
```

---

## Ready to Test?

1. ✓ Read this file (you're here!)
2. Start services: `./start-services-for-testing.sh`
3. Run pre-test: `./pre-test-verification.sh` (optional)
4. Open: `MANUAL_TESTING_GUIDE.md`
5. Follow all test scenarios
6. Check off all items in checklist
7. Commit and update plan when done

**Good luck! 🚀**
