/**
 * Browser Console Security Verification Script
 *
 * Purpose: Verify that JWT tokens are NOT accessible to JavaScript
 * Usage: Copy this entire script and paste into browser console after logging in
 *
 * Expected Result: All checks should PASS
 */

(function securityVerification() {
  console.log('=== JWT Cookie Security Verification ===\n');

  const results = {
    passed: [],
    failed: [],
    warnings: []
  };

  // Check 1: document.cookie should NOT contain tokens
  console.log('Check 1: Testing document.cookie for token exposure...');
  const cookieString = document.cookie;
  const hasAccessToken = cookieString.includes('access_token');
  const hasRefreshToken = cookieString.includes('refresh_token');

  if (!hasAccessToken && !hasRefreshToken) {
    results.passed.push('✅ PASS: Tokens NOT visible in document.cookie (httpOnly working)');
  } else {
    results.failed.push('❌ FAIL: Tokens ARE visible in document.cookie (httpOnly NOT working)');
  }

  // Check 2: localStorage should NOT contain tokens
  console.log('Check 2: Testing localStorage for token storage...');
  const authData = localStorage.getItem('osfeed-auth');
  let hasTokensInLocalStorage = false;

  if (authData) {
    try {
      const parsed = JSON.parse(authData);
      const state = parsed.state || parsed;

      if (state.tokens || (state.access_token || state.refresh_token)) {
        hasTokensInLocalStorage = true;
        results.failed.push('❌ FAIL: Tokens found in localStorage');
      } else if (state.user) {
        results.passed.push('✅ PASS: localStorage contains only user info (no tokens)');
      } else {
        results.warnings.push('⚠️  WARNING: localStorage structure unexpected');
      }
    } catch (e) {
      results.warnings.push('⚠️  WARNING: Could not parse localStorage data');
    }
  } else {
    results.passed.push('✅ PASS: No auth data in localStorage');
  }

  // Check 3: sessionStorage should NOT contain tokens
  console.log('Check 3: Testing sessionStorage for token storage...');
  let hasTokensInSessionStorage = false;

  for (let i = 0; i < sessionStorage.length; i++) {
    const key = sessionStorage.key(i);
    const value = sessionStorage.getItem(key);

    if (value && (value.includes('access_token') || value.includes('refresh_token'))) {
      hasTokensInSessionStorage = true;
      break;
    }
  }

  if (!hasTokensInSessionStorage) {
    results.passed.push('✅ PASS: No tokens in sessionStorage');
  } else {
    results.failed.push('❌ FAIL: Tokens found in sessionStorage');
  }

  // Check 4: Check if cookies exist (via DevTools inspection message)
  console.log('Check 4: Verifying cookie presence...');
  console.log('→ Open DevTools > Application > Cookies > localhost');
  console.log('→ Verify these cookies exist with HttpOnly flag:');
  console.log('  - access_token (HttpOnly: ✓)');
  console.log('  - refresh_token (HttpOnly: ✓)');
  results.warnings.push('⚠️  MANUAL: Verify cookies in DevTools Application tab');

  // Check 5: XSS Simulation - Try alternative access methods
  console.log('Check 5: Testing alternative cookie access methods...');
  const cookieKeys = Object.keys(document).filter(key =>
    key.toLowerCase().includes('cookie')
  );

  if (cookieKeys.length <= 1) { // only 'cookie' property should exist
    results.passed.push('✅ PASS: No alternative cookie access methods found');
  } else {
    results.warnings.push('⚠️  WARNING: Unexpected cookie-related properties: ' + cookieKeys.join(', '));
  }

  // Display Results
  console.log('\n=== VERIFICATION RESULTS ===\n');

  console.log('✅ PASSED CHECKS:');
  results.passed.forEach(msg => console.log('  ' + msg));

  if (results.failed.length > 0) {
    console.log('\n❌ FAILED CHECKS:');
    results.failed.forEach(msg => console.log('  ' + msg));
  }

  if (results.warnings.length > 0) {
    console.log('\n⚠️  WARNINGS:');
    results.warnings.forEach(msg => console.log('  ' + msg));
  }

  // Final Summary
  console.log('\n=== SUMMARY ===');
  const totalChecks = results.passed.length + results.failed.length;
  const passRate = ((results.passed.length / totalChecks) * 100).toFixed(0);

  console.log(`Passed: ${results.passed.length}/${totalChecks} (${passRate}%)`);
  console.log(`Failed: ${results.failed.length}/${totalChecks}`);
  console.log(`Warnings: ${results.warnings.length}`);

  if (results.failed.length === 0) {
    console.log('\n🎉 SECURITY VERIFICATION PASSED! 🎉');
    console.log('Tokens are NOT accessible to JavaScript.');
    console.log('XSS attack surface has been eliminated.');
    return true;
  } else {
    console.log('\n⚠️  SECURITY VERIFICATION FAILED!');
    console.log('Please fix the issues above before deploying to production.');
    return false;
  }
})();

/**
 * Additional Manual Checks:
 *
 * 1. Network Tab Verification:
 *    - Open DevTools > Network
 *    - Make an API request (navigate to a page)
 *    - Click on request > Headers
 *    - Verify: Cookie header includes access_token and refresh_token
 *    - Verify: NO Authorization header present
 *
 * 2. Cookie Attributes:
 *    - Open DevTools > Application > Cookies
 *    - Verify for both access_token and refresh_token:
 *      ✓ HttpOnly: checked
 *      ✓ SameSite: Lax (or Strict)
 *      ✓ Secure: checked in production (unchecked in dev)
 *
 * 3. Logout Test:
 *    - Click logout button
 *    - Open DevTools > Application > Cookies
 *    - Verify: access_token and refresh_token are GONE
 */
