# Manual Testing Procedure - ErrorBoundary i18n Verification

## Test ID: subtask-3-1
**Description:** Test error boundary in English language mode
**Date:** 2026-02-04
**Component:** ErrorBoundary (frontend/src/components/common/error-boundary.tsx)

---

## Prerequisites

1. Frontend dev server must be running (`cd frontend && npm run dev`)
2. Browser with JavaScript console access
3. Test component available for triggering errors

---

## Test Setup

### Option 1: Using Test Component (Recommended)

1. Add the ErrorTrigger component to a test page:
   ```typescript
   import { ErrorTrigger } from '@/components/test/ErrorTrigger'

   // Add to any page component:
   <ErrorTrigger />
   ```

2. The ErrorTrigger component will appear as a red button in the bottom-right corner

### Option 2: Using Browser Console

1. Open browser DevTools (F12 or Cmd+Option+I)
2. Navigate to Console tab
3. Execute: `throw new Error('Test error')`

### Option 3: Temporary Component Modification

1. Add this code to any component:
   ```typescript
   const [throwError, setThrowError] = useState(false)
   if (throwError) throw new Error('Test error')

   <button onClick={() => setThrowError(true)}>Trigger Error</button>
   ```

---

## Test Steps - English Mode

### Step 1: Start Frontend Dev Server
```bash
cd frontend
npm run dev
```

Expected: Dev server starts on http://localhost:5173

### Step 2: Set Language to English

1. Navigate to http://localhost:5173
2. Click on Settings/Preferences (gear icon or menu)
3. Find Language selector
4. Select "English" or "EN"
5. Verify page content updates to English

### Step 3: Trigger an Error

Using your chosen method from Test Setup:
- Click "Trigger Error" button (ErrorTrigger component), or
- Execute `throw new Error('Test')` in console, or
- Click the test button in your modified component

### Step 4: Verify Error Boundary UI

When the error boundary activates, verify the following text appears in **ENGLISH**:

| UI Element | Expected English Text | Translation Key |
|------------|----------------------|-----------------|
| Title | "Something went wrong" | common.errorTitle |
| Retry Button | "Try again" | common.errorRetry |
| Reconnect Button | "Reconnect" | common.errorReconnect |
| Error Message | "Unknown error" or custom message | common.errorUnknown |

**❌ FAIL CONDITIONS:**
- If ANY French text appears ("Une erreur s'est produite", "Réessayer", "Se reconnecter")
- If text is missing or blank
- If buttons don't render properly

**✅ PASS CONDITIONS:**
- All text is in English
- All 4 translation keys render correctly
- UI is properly styled and functional
- Retry button resets the error state
- Reconnect button navigates to /login

---

## Expected Results

### Visual Verification Checklist

- [ ] **Title:** "Something went wrong" (NOT "Une erreur s'est produite")
- [ ] **Button 1:** "Try again" (NOT "Réessayer")
- [ ] **Button 2:** "Reconnect" (NOT "Se reconnecter")
- [ ] **Error Message:** Shows actual error message or "Unknown error" (NOT "Erreur inconnue")
- [ ] **Layout:** Centered on page with proper styling
- [ ] **Functionality:** Buttons are clickable and functional

### Translation Keys Used (for reference)

From `frontend/src/locales/en/common.json`:
```json
{
  "errorTitle": "Something went wrong",
  "errorRetry": "Try again",
  "errorReconnect": "Reconnect",
  "errorUnknown": "Unknown error"
}
```

---

## Test Evidence Documentation

### Screenshot Locations
- `./test-screenshots/error-boundary-english-mode.png` (if captured)

### Browser Console Output
Record any relevant console messages:
```
ErrorBoundary caught an error: [error details]
```

### Test Result
- **Status:** ✅ PASS / ❌ FAIL
- **Language Tested:** English (EN)
- **Date:** 2026-02-04
- **Notes:** [Any observations]

---

## Troubleshooting

### Issue: French text still appears
**Cause:** Language setting not applied
**Solution:** Clear browser localStorage and refresh page, then set language again

### Issue: Error boundary doesn't catch error
**Cause:** Error thrown outside component tree
**Solution:** Ensure error is thrown inside a component wrapped by ErrorBoundary

### Issue: Translation keys not found
**Cause:** i18n not initialized properly
**Solution:** Verify I18nextProvider is wrapping ErrorBoundary in providers.tsx

### Issue: Dev server won't start
**Cause:** Dependencies not installed or port conflict
**Solution:** Run `npm install` and check if port 5173 is available

---

## Code Verification (Already Completed)

✅ ErrorBoundary uses `withTranslation()` HOC
✅ All strings use `this.props.t('common.*')` translation keys
✅ Translation keys exist in `en/common.json`
✅ ErrorBoundary wrapped in I18nextProvider
✅ No hardcoded French strings in component code

---

## Related Tests

- **Next Test:** subtask-3-2 - Test error boundary in French language mode
- **Previous Tests:** Phase 1 verification subtasks (all completed)

---

## Notes for Tester

This manual test verifies that the fix implemented in commit `bae2e64` is working correctly in production. The ErrorBoundary component should display all text in the user's selected language (English for this test), NOT hardcoded French text.

The test is simple but critical: ensure error messages respect the user's language preference.
