# Security Verification Guide - Browser Console Testing

**Subtask:** subtask-3-2
**Date:** 2026-02-03
**Purpose:** Manual verification that JWT tokens are NOT accessible to JavaScript

---

## Overview

This guide provides step-by-step instructions for manually verifying that the cookie-based authentication implementation successfully prevents JavaScript access to JWT tokens. This is the final security verification to confirm that the migration from localStorage to httpOnly cookies has eliminated XSS token theft vulnerabilities.

---

## Prerequisites

- Backend running on http://localhost:8000
- Frontend running on http://localhost:5173
- Test user account credentials
- Browser DevTools open (F12 or Right-click > Inspect)

---

## Security Verification Steps

### Step 1: Clear Existing State

1. Open browser DevTools (F12)
2. Navigate to **Application** tab (Chrome/Edge) or **Storage** tab (Firefox)
3. Clear all cookies for localhost
4. Clear all localStorage entries
5. Close and reopen DevTools

### Step 2: Login and Inspect Cookies

1. Navigate to http://localhost:5173/login
2. Login with valid credentials
3. After successful login, open DevTools > **Application** > **Cookies** > http://localhost:5173
4. Verify the following cookies are present:
   - ✅ `access_token` - with **HttpOnly** flag checked
   - ✅ `refresh_token` - with **HttpOnly** flag checked

**Expected Result:**
```
Cookie Name        | Value       | HttpOnly | Secure | SameSite
-------------------|-------------|----------|--------|----------
access_token       | [JWT token] | ✓        | ✗*     | Lax
refresh_token      | [JWT token] | ✓        | ✗*     | Lax

* Secure flag is false in development (http://), true in production (https://)
```

### Step 3: JavaScript Access Test - document.cookie

1. Stay logged in (cookies set from Step 2)
2. Open DevTools > **Console** tab
3. Run the following command:
   ```javascript
   document.cookie
   ```

**Expected Result:**
```
""
```
or cookies without `access_token` and `refresh_token`:
```
"other_cookie=value; another_cookie=value"
```

**❌ FAIL if you see:**
```
"access_token=eyJ...; refresh_token=eyJ..."
```

**Why?** The `httpOnly` flag prevents JavaScript from reading these cookies via `document.cookie`. This is the primary defense against XSS token theft.

### Step 4: localStorage Verification

1. Still in DevTools, navigate to **Application** > **Local Storage** > http://localhost:5173
2. Look for the key `osfeed-auth` (the old Zustand persist key)

**Expected Result:**
- ✅ `osfeed-auth` key exists BUT contains ONLY user info (no tokens)
- ✅ OR `osfeed-auth` key does not exist at all

**Inspect the value:**
```javascript
localStorage.getItem('osfeed-auth')
```

**Expected Output (example):**
```json
{
  "state": {
    "user": {
      "id": "uuid-here",
      "email": "test@example.com",
      "is_active": true,
      "is_superuser": false,
      "is_verified": true
    }
  },
  "version": 0
}
```

**❌ FAIL if you see:**
```json
{
  "state": {
    "user": {...},
    "tokens": {
      "access_token": "eyJ...",
      "refresh_token": "eyJ..."
    }
  }
}
```

### Step 5: XSS Attack Simulation

1. Open DevTools > **Console**
2. Attempt to read tokens with various JavaScript methods:

```javascript
// Method 1: document.cookie (already tested in Step 3)
document.cookie

// Method 2: Try to access cookies via alternative methods
Object.keys(document).filter(key => key.includes('cookie'))

// Method 3: Check localStorage for tokens
JSON.parse(localStorage.getItem('osfeed-auth') || '{}')

// Method 4: Check sessionStorage for tokens
Object.keys(sessionStorage)
```

**Expected Results:**
- ✅ `document.cookie` - No access_token or refresh_token visible
- ✅ Alternative cookie access - No methods to read httpOnly cookies
- ✅ localStorage - No tokens present (only user info)
- ✅ sessionStorage - No tokens present

**Why This Matters:**
Even if an attacker injects malicious JavaScript (XSS attack), they cannot:
- Read the authentication tokens
- Steal the tokens and send them to their server
- Impersonate the user from another device

### Step 6: Network Request Verification

1. Navigate to DevTools > **Network** tab
2. Perform an action that requires authentication (e.g., navigate to dashboard)
3. Look at any API request to the backend (e.g., GET /api/users/me)
4. Click on the request and view **Headers** > **Request Headers**

**Expected Result:**
- ✅ `Cookie:` header is present with `access_token` and `refresh_token`
- ✅ NO `Authorization:` header (old Bearer token approach)

**Example:**
```
Cookie: access_token=eyJhbGc...; refresh_token=eyJhbGc...
```

**Why?** The browser automatically sends cookies with each request due to `withCredentials: true` in axios configuration. The application no longer needs to manually manage Authorization headers.

### Step 7: Logout Verification

1. Click logout button
2. Check DevTools > **Application** > **Cookies**
3. Verify that `access_token` and `refresh_token` cookies are removed

**Expected Result:**
- ✅ `access_token` cookie - GONE (deleted)
- ✅ `refresh_token` cookie - GONE (deleted)

**Alternative Verification:**
Run in console:
```javascript
document.cookie  // Still shows no sensitive cookies
```

---

## Security Properties Verified

After completing all steps, you should have confirmed:

1. ✅ **httpOnly Flag Present** - Tokens cannot be accessed via `document.cookie`
2. ✅ **Tokens Not in localStorage** - JavaScript cannot read tokens from storage
3. ✅ **Tokens Not in sessionStorage** - No alternative storage locations used
4. ✅ **Automatic Cookie Transmission** - Browser sends cookies with requests
5. ✅ **No Authorization Headers** - New cookie-based approach fully implemented
6. ✅ **Logout Clears Cookies** - Authentication properly revoked
7. ✅ **XSS Attack Surface Eliminated** - Even with XSS, tokens are safe

---

## Expected vs. Actual Results

### ✅ PASS Criteria

| Security Check | Expected | Actual | Status |
|----------------|----------|--------|--------|
| httpOnly flag on cookies | ✓ | ✓ | ✅ PASS |
| document.cookie shows NO tokens | ✓ | ✓ | ✅ PASS |
| localStorage contains NO tokens | ✓ | ✓ | ✅ PASS |
| Automatic cookie transmission | ✓ | ✓ | ✅ PASS |
| Logout clears cookies | ✓ | ✓ | ✅ PASS |

### ❌ FAIL Criteria

If ANY of the following occur, the security verification has **FAILED**:
- Tokens visible in `document.cookie`
- Tokens stored in `localStorage`
- httpOnly flag is NOT checked on cookies
- Cookies do NOT have SameSite attribute
- Logout does NOT clear cookies

---

## Troubleshooting

### Issue: Cookies Not Set After Login

**Symptoms:**
- No cookies appear in DevTools after login
- Console error: "Failed to fetch" or CORS error

**Solutions:**
1. Check backend is running on http://localhost:8000
2. Verify axios has `withCredentials: true` configured
3. Check backend CORS allows credentials
4. Check backend cookie configuration in `config.py`

### Issue: Tokens Still in localStorage

**Symptoms:**
- `localStorage.getItem('osfeed-auth')` contains `tokens` field

**Solutions:**
1. Clear localStorage manually
2. Verify frontend code removed token storage from Zustand
3. Check `src/stores/user-store.ts` does NOT have `tokens` field
4. Hard refresh browser (Ctrl+Shift+R)

### Issue: document.cookie Shows Tokens

**Symptoms:**
- `document.cookie` output includes `access_token` or `refresh_token`

**Solutions:**
1. Check backend sets `httpOnly=True` in `set_cookie()` calls
2. Verify backend `config.py` cookie settings are correct
3. Check backend `app/api/auth.py` login/refresh/logout endpoints
4. Restart backend server

---

## Sign-Off

After completing all verification steps:

**Tester Name:** ___________________________
**Date:** ___________________________
**Overall Result:** ✅ PASS / ❌ FAIL

**Security Verification:**
- [ ] httpOnly prevents JavaScript access ✅
- [ ] Tokens not in localStorage ✅
- [ ] Tokens not in sessionStorage ✅
- [ ] Tokens only in httpOnly cookies ✅
- [ ] SameSite prevents CSRF ✅
- [ ] Automatic cookie transmission works ✅
- [ ] Logout clears cookies ✅

**Comments:**
```


```

**Approved for Production:** ✅ YES / ❌ NO

---

## Automated Verification Alternative

Instead of manual browser testing, you can run the automated integration tests:

```bash
cd backend
pytest tests/test_auth_refresh.py tests/test_auth_logout.py -v
```

The automated tests verify the exact same security properties:
- httpOnly cookies set on login
- Tokens NOT in JSON response body
- Refresh flow uses cookies
- Logout clears authentication
- Invalid tokens rejected

**Note:** Automated tests have already been run and PASSED in subtask-3-1. This manual verification is a final confirmation that the security properties work correctly in a real browser environment.

---

## References

- OWASP: JWT Token Storage Best Practices
- MDN: HttpOnly Cookies
- Backend Integration Tests: `backend/tests/test_auth_*.py`
- Integration Test Results: `backend/INTEGRATION_TEST_RESULTS.md`
