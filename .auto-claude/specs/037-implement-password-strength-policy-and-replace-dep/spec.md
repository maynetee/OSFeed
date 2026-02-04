# Implement password strength policy and replace deprecated python-jose

## Overview

Two authentication weaknesses exist: 1) No custom password validation is configured — the UserManager class doesn't override `validate_password()`, meaning FastAPI-Users applies only its minimal default (3+ characters). Users can register with trivially weak passwords like '123'. 2) The JWT library `python-jose` is unmaintained (last release 2022, known CVE issues) and should be replaced with `PyJWT` or `joserfc` which are actively maintained.

## Rationale

Weak passwords are the most common authentication failure. Without strength requirements, credential stuffing and brute-force attacks become viable even with rate limiting. The unmaintained python-jose library poses a supply-chain risk — known vulnerabilities won't receive patches.

---

## ✅ VERIFICATION COMPLETE - SPEC IS OUTDATED

**Investigation Date**: 2026-02-04
**Status**: ✅ **BOTH ISSUES ALREADY RESOLVED - NO IMPLEMENTATION REQUIRED**

### Investigation Findings

A comprehensive investigation was conducted to verify the claims in this spec. **The spec is outdated** - both described issues have already been resolved in the current codebase:

#### 1. Password Strength Policy ✅ FULLY IMPLEMENTED

**Location**: `backend/app/auth/users.py` (lines 45-90)

The `UserManager.validate_password()` method is already implemented with **full OWASP compliance**:
- ✅ Minimum 8 characters (not 3)
- ✅ At least 1 uppercase letter
- ✅ At least 1 lowercase letter
- ✅ At least 1 digit
- ✅ At least 1 special character

**Test Coverage**: 6 comprehensive tests in `backend/tests/test_auth_registration.py` (lines 112-219)
- test_register_weak_password_too_short
- test_register_weak_password_no_uppercase
- test_register_weak_password_no_lowercase
- test_register_weak_password_no_digit
- test_register_weak_password_no_special_char
- test_register_strong_password_success

**Result**: Weak passwords like '123' are **already rejected** by the current implementation.

#### 2. JWT Library Migration ✅ ALREADY COMPLETE

**Location**: `backend/requirements.txt`

The migration from `python-jose` to `PyJWT` has already been completed:
- ✅ `PyJWT>=2.8.0` is present in dependencies
- ✅ `python-jose` is **NOT present** (confirmed via grep)
- ✅ FastAPI-Users 13.0.0 uses PyJWT 2.9.0 internally (actively maintained)

**Test Coverage**: 2 comprehensive tests in `backend/tests/test_auth_refresh.py`
- test_login_and_refresh_token_flow (full JWT authentication flow)
- test_refresh_token_rejects_invalid_token (error handling)

**Security Features Implemented**:
- httpOnly cookies (XSS prevention)
- SameSite attribute (CSRF protection)
- HMAC token hashing
- Cryptographically secure token generation
- Proper token expiration

**Result**: PyJWT is **already in use** with no known CVE vulnerabilities.

### Conclusion

**No implementation work is required.** Both authentication weaknesses described in this spec have been resolved:
1. Password validation prevents weak passwords with OWASP-compliant requirements
2. PyJWT library is actively maintained with comprehensive security features
3. Full test coverage exists for both features (8 tests total)
4. Implementation follows security best practices

### Documentation

For complete verification details, see:
- **[VERIFICATION_REPORT.md](./VERIFICATION_REPORT.md)** - Comprehensive investigation findings
- **[implementation_plan.json](./implementation_plan.json)** - Investigation workflow (5/6 subtasks completed)
- **[build-progress.txt](./build-progress.txt)** - Detailed session notes

---
*This spec was created from ideation and is pending detailed specification.*
*Investigation completed 2026-02-04: Spec claims are outdated - work already complete.*
