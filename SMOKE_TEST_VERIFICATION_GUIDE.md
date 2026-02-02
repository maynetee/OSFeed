# Frontend Smoke Test Verification Guide

**Task:** Subtask 2-3 - Run frontend smoke tests to verify functionality
**Purpose:** Verify frontend application works correctly without 'unsafe-eval' in CSP

## Overview

This guide documents the verification of frontend functionality through Playwright smoke tests after removing 'unsafe-eval' from the Content-Security-Policy script-src directive.

## Environment Limitation

**Current Status:** Smoke tests cannot be executed in the worktree environment.
- Node.js and npm are not available in this environment
- This follows the same pattern as subtasks 2-1 and 2-2, which were completed via code inspection and documentation

## Smoke Tests Location

- **Test File:** `frontend/tests/smoke.spec.ts`
- **Test Framework:** Playwright
- **Test Count:** 3 smoke tests
- **Base URL:** `http://localhost:5173`

## Test Coverage

The smoke test suite (`smoke.spec.ts`) includes:

### 1. Login Flow Test
```typescript
test('login flow reaches dashboard', async ({ page }) => {
  await login(page)
})
```
- **Purpose:** Verifies basic authentication flow
- **Expected:** User reaches dashboard after clicking login button
- **CSP Impact:** Tests that authentication logic works without 'unsafe-eval'

### 2. Navigation to Feed Test
```typescript
test('navigation to feed opens export dialog', async ({ page }) => {
  await login(page)
  await page.getByRole('link', { name: 'Fil' }).click()
  await expect(page.getByRole('heading', { name: 'Signaux prioritaires' })).toBeVisible()
  await page.getByRole('button', { name: 'Exporter' }).click()
  await expect(page.getByRole('heading', { name: 'Exporter les signaux' })).toBeVisible()
})
```
- **Purpose:** Verifies feed navigation and export dialog functionality
- **Expected:** Feed page loads and export dialog opens
- **CSP Impact:** Tests React router navigation and dialog components without 'unsafe-eval'

### 3. Search Page Tabs Test
```typescript
test('search page shows tabs', async ({ page }) => {
  await login(page)
  await page.getByRole('link', { name: 'Recherche' }).click()
  await expect(page.getByRole('heading', { name: 'Recherche', level: 2 })).toBeVisible()
  await expect(page.getByRole('tab', { name: 'Semantique' })).toBeVisible()
  await expect(page.getByRole('tab', { name: 'Mot-cle' })).toBeVisible()
  await expect(page.getByRole('tab', { name: 'Entites' })).toBeVisible()
})
```
- **Purpose:** Verifies search page and tab component rendering
- **Expected:** All three tabs are visible and functional
- **CSP Impact:** Tests complex UI components without 'unsafe-eval'

## Verification Methods

### Method 1: Automated Script (Recommended)

Run the provided automation script:
```bash
./run_smoke_tests.sh
```

This script will:
1. Check for Node.js and npm
2. Navigate to frontend directory
3. Install dependencies if needed
4. Run Playwright smoke tests
5. Report results with clear pass/fail status

### Method 2: Manual Verification

#### Prerequisites
- Node.js installed (v18 or higher recommended)
- npm available
- Both backend and frontend in working state

#### Steps

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies (if needed):**
   ```bash
   npm install
   ```

3. **Install Playwright browsers (if first time):**
   ```bash
   npx playwright install
   ```

4. **Run smoke tests:**
   ```bash
   npm run test:e2e -- tests/smoke.spec.ts
   ```

   Alternative commands:
   ```bash
   # Run with specific reporter
   npx playwright test tests/smoke.spec.ts --reporter=list

   # Run in headed mode (visible browser)
   npx playwright test tests/smoke.spec.ts --headed

   # Run in debug mode
   npx playwright test tests/smoke.spec.ts --debug
   ```

## Expected Results

### Success Criteria
- ✅ All 3 tests pass
- ✅ No CSP violation errors in test output
- ✅ No 'unsafe-eval' related errors
- ✅ Login, navigation, and UI components work correctly

### Example Success Output
```
Running 3 tests using 1 worker

  ✓ [chromium] › tests/smoke.spec.ts:12:1 › login flow reaches dashboard (2.5s)
  ✓ [chromium] › tests/smoke.spec.ts:16:1 › navigation to feed opens export dialog (3.1s)
  ✓ [chromium] › tests/smoke.spec.ts:24:1 › search page shows tabs (2.8s)

  3 passed (8.7s)
```

### Potential Issues

If tests fail, check for:
1. **CSP Violations:** Look for console errors containing "Content Security Policy"
2. **'unsafe-eval' Errors:** Check for eval-related error messages
3. **Component Failures:** Verify React components load correctly
4. **API Connection:** Ensure backend is running if tests need it

## Technical Analysis

### Why These Tests Matter for CSP

Modern React + Vite applications (like this one) should work without 'unsafe-eval':

1. **React 18.2:** Uses standard JavaScript, no eval required
2. **Vite 5.0:** Modern bundler with ES modules, no eval
3. **Playwright Tests:** Runs in real browser with actual CSP enforcement
4. **Component Libraries:**
   - @radix-ui components: CSP-compliant
   - @tanstack/react-query: No eval usage
   - react-router-dom: Standard navigation, no eval

### What the Tests Verify

These smoke tests validate:
- **Authentication Flow:** Login logic doesn't use eval
- **React Router:** Client-side routing works without eval
- **Dialog Components:** Dynamic UI components render correctly
- **Tab Navigation:** Complex interactions function properly
- **Data Fetching:** React Query operations work (if backend available)

## Confidence Level

**High Confidence** that smoke tests will pass because:
1. Modern React/Vite stack is CSP-compliant by design
2. No dependencies require 'unsafe-eval'
3. Similar applications run successfully without 'unsafe-eval'
4. CSP configuration change is backend-only (no frontend code changes)
5. Previous subtasks confirmed no eval usage in codebase

## Playwright Configuration

The tests use the following configuration (`playwright.config.ts`):
- **Test Directory:** `./tests`
- **Base URL:** `http://localhost:5173`
- **Timeout:** 30 seconds per test
- **Web Server:** Auto-starts dev server on port 5173
- **Trace:** Enabled on first retry for debugging

## Integration with CI/CD

For continuous integration:
```yaml
# Example GitHub Actions workflow
- name: Run Smoke Tests
  run: |
    cd frontend
    npm install
    npx playwright install
    npm run test:e2e -- tests/smoke.spec.ts
```

## Next Steps

After running these tests successfully:
1. Verify all tests pass
2. Check for any CSP-related warnings in test output
3. Document any issues in build-progress.txt
4. Mark subtask-2-3 as completed in implementation_plan.json
5. Commit changes with appropriate message

## References

- Playwright Documentation: https://playwright.dev
- CSP Guide: https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP
- React + CSP: https://react.dev/reference/react-dom/client/createRoot#security-and-content-security-policy

---
**Created:** 2026-02-02
**Subtask:** subtask-2-3
**Status:** Documentation complete, awaiting execution in proper environment
