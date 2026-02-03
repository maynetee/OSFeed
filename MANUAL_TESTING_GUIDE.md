# Manual Browser Testing Guide
## Cookie-Based Authentication End-to-End Testing

**Task:** Subtask-3-1 - Manual browser testing of complete auth flow
**Date:** 2026-02-03

---

## Prerequisites

Before starting the tests, ensure both services are running:

### 1. Start Backend Server
```bash
cd backend
source venv/bin/activate  # or your virtual environment
uvicorn app.main:app --reload --port 8000
```

Verify backend is running: http://localhost:8000/docs

### 2. Start Frontend Development Server
```bash
cd frontend
npm run dev
```

Verify frontend is running: http://localhost:5173

---

## Test Scenario 1: Login Flow with Cookie Verification

### Steps:

1. **Open Browser DevTools**
   - Open Chrome/Firefox/Safari
   - Press F12 or right-click > Inspect
   - Go to **Application** tab (Chrome) or **Storage** tab (Firefox)
   - Navigate to **Cookies** section

2. **Navigate to Login Page**
   - URL: http://localhost:5173/login
   - Verify login form renders without errors

3. **Login with Test Credentials**
   - Enter test username/email
   - Enter test password
   - Click Login button
   - Verify successful login (redirect to dashboard/home)

4. **Verify Cookies Are Set**
   - In DevTools > Application > Cookies > http://localhost:5173
   - **Verify the following cookies exist:**
     - ✅ `access_token`
     - ✅ `refresh_token`
   - **Verify cookie attributes:**
     - ✅ `HttpOnly` flag is checked/enabled
     - ✅ `SameSite` is set to `Lax`
     - ✅ `Secure` is `false` (for local development) or `true` (for production)
     - ✅ `Path` is `/`
     - ✅ `Domain` matches your localhost

5. **Verify localStorage Does NOT Contain Tokens**
   - In DevTools > Application > Local Storage > http://localhost:5173
   - Look for key: `osfeed-auth`
   - **Verify:**
     - ✅ localStorage contains user info (id, email, etc.)
     - ✅ localStorage does NOT contain `access_token` field
     - ✅ localStorage does NOT contain `refresh_token` field
     - ✅ No `tokens` object in localStorage

---

## Test Scenario 2: Protected Page Access

### Steps:

1. **Navigate to Protected Page**
   - After successful login, navigate to a protected route (e.g., dashboard, profile)
   - **Verify:**
     - ✅ Page loads successfully
     - ✅ No authentication errors
     - ✅ User is authenticated and sees protected content

2. **Check Network Requests**
   - In DevTools > Network tab
   - Make an API request (navigate to a page that calls the backend)
   - Click on any API request to backend
   - Go to **Headers** section
   - **Verify:**
     - ✅ `Cookie` header is present in **Request Headers**
     - ✅ Cookie header contains `access_token=...`
     - ✅ NO `Authorization: Bearer ...` header in Request Headers

---

## Test Scenario 3: Token Refresh Flow

### Steps:

1. **Simulate Token Expiration**
   - **Option A - Wait for expiration:** Wait 60 minutes for access token to expire naturally
   - **Option B - Manual deletion:**
     - In DevTools > Application > Cookies
     - Find `access_token` cookie
     - Right-click > Delete
     - Keep `refresh_token` cookie intact

2. **Make an API Request**
   - Navigate to a different page or refresh the current page
   - This will trigger an API request with expired/missing access token
   - **Verify:**
     - ✅ Page loads successfully (no authentication error)
     - ✅ In Network tab, you should see:
       - First request returns 401 Unauthorized
       - Automatic call to `/api/auth/refresh`
       - Retry of original request succeeds
     - ✅ New `access_token` cookie is set
     - ✅ New `refresh_token` cookie is set

3. **Verify Automatic Refresh Worked**
   - In DevTools > Application > Cookies
   - **Verify:**
     - ✅ `access_token` cookie exists again
     - ✅ User remains logged in
     - ✅ No errors in console

---

## Test Scenario 4: Logout Flow

### Steps:

1. **Click Logout Button**
   - Find and click the logout button in the UI
   - **Verify:**
     - ✅ Redirected to login page or home page
     - ✅ No console errors

2. **Verify Cookies Are Cleared**
   - In DevTools > Application > Cookies
   - **Verify:**
     - ✅ `access_token` cookie is deleted/not present
     - ✅ `refresh_token` cookie is deleted/not present

3. **Verify Cannot Access Protected Pages**
   - Try to navigate to a protected route (e.g., /dashboard)
   - **Verify:**
     - ✅ Redirected to login page
     - ✅ OR see "Unauthorized" message
     - ✅ Cannot access protected content

---

## Test Scenario 5: Security Verification

### Steps:

1. **Verify Cookies Are NOT Accessible to JavaScript**
   - After logging in, open DevTools > Console
   - Run command: `document.cookie`
   - **Verify:**
     - ✅ `access_token` is NOT visible in output
     - ✅ `refresh_token` is NOT visible in output
     - ✅ Only non-httpOnly cookies (if any) are visible
   - This confirms httpOnly flag is working

2. **Verify Tokens Are NOT in localStorage**
   - Open DevTools > Application > Local Storage
   - Look at `osfeed-auth` key
   - **Verify:**
     - ✅ No `access_token` property
     - ✅ No `refresh_token` property
     - ✅ No `tokens` object
     - ✅ Only user info (id, email, is_active, etc.) is stored

3. **Verify Network Requests Use Cookies**
   - In DevTools > Network tab
   - Make any authenticated API request
   - Click on request > Headers tab
   - **Verify:**
     - ✅ `Cookie` header present in Request Headers
     - ✅ Cookies are sent automatically (withCredentials: true)
     - ✅ NO Authorization header with Bearer token

---

## Test Results Checklist

After completing all scenarios, verify all items below:

### Cookies Configuration
- [ ] `access_token` cookie set on login
- [ ] `refresh_token` cookie set on login
- [ ] Both cookies have `HttpOnly` flag enabled
- [ ] Both cookies have `SameSite=Lax`
- [ ] Both cookies have correct `Path=/`
- [ ] Cookies are cleared on logout

### localStorage Security
- [ ] NO tokens stored in localStorage
- [ ] Only user info in localStorage
- [ ] `osfeed-auth` key does not contain `tokens` object

### JavaScript Inaccessibility
- [ ] `document.cookie` does NOT show access_token
- [ ] `document.cookie` does NOT show refresh_token
- [ ] Tokens are protected from XSS attacks

### Authentication Flow
- [ ] Login sets cookies correctly
- [ ] Protected pages accessible when authenticated
- [ ] Token refresh works automatically
- [ ] Logout clears cookies
- [ ] Cannot access protected pages after logout

### Network Behavior
- [ ] API requests send cookies automatically
- [ ] NO Authorization: Bearer headers
- [ ] Refresh endpoint called on 401
- [ ] Original request retried after refresh

---

## Troubleshooting

### Issue: Cookies not showing in DevTools
- **Solution:** Make sure you're looking at the right domain (http://localhost:5173)
- Check Network tab > Response Headers for `Set-Cookie`

### Issue: "withCredentials" CORS error
- **Solution:** Verify backend has CORS configured with credentials support
- Check `allow_credentials=True` in FastAPI CORS middleware

### Issue: Refresh token flow not working
- **Solution:** Check Network tab for 401 responses
- Verify refresh endpoint is being called
- Check console for any JavaScript errors

### Issue: Cookies not cleared on logout
- **Solution:** Check Network tab > logout response headers
- Should see `Set-Cookie` with `Max-Age=0` or `Expires` in past

---

## Completion Criteria

All scenarios must pass (all checkboxes checked) before marking subtask as complete.

If any test fails:
1. Document the failure in build-progress.txt
2. Debug and fix the issue
3. Re-run all tests
4. Only mark complete when all tests pass

---

## Notes

- Test in Chrome, Firefox, or Safari
- Use Private/Incognito mode to ensure clean state
- Clear cookies between test runs if needed
- Document any unexpected behavior

---

## Sign-off

**Tester:** _________________
**Date:** _________________
**Result:** PASS / FAIL
**Notes:**

_____________________________________________
_____________________________________________
_____________________________________________
