# Exception Audit - Bare `except Exception` Catches

**Generated:** 2026-02-04
**Total Instances Found:** 18 across 14 files
**Note:** The spec mentioned 51 instances, but current codebase shows 18. Some may have been refactored already.

---

## Summary by Category

| Category | Count | Files |
|----------|-------|-------|
| API Endpoints | 7 | auth.py, channels.py, alerts.py, messages.py (2), collections.py |
| Services | 4 | channel_utils.py, llm_translator.py, message_media_service.py, auth_rate_limiter.py |
| Auth/Email | 3 | users.py (3) |
| CLI Tools | 2 | telegram_setup.py, verify_gin_index.py (2) |
| Main App | 1 | main.py |
| Utilities | 1 | retry.py (INTENTIONAL - keep as is) |

---

## Detailed Audit

### 1. API Endpoints

#### 1.1 `backend/app/api/auth.py:85`
**Context:** User registration endpoint
**Current Code:**
```python
except (SQLAlchemyError, IntegrityError) as e:
    # ... database error handling
except Exception as e:
    logger.error(f"Registration failed with unexpected error: {e}")
    raise HTTPException(status_code=500, detail="REGISTER_UNEXPECTED_ERROR")
```

**Recommendation:**
- **Option 1:** Replace with `ValueError` and `TypeError` for data validation errors
- **Option 2:** Keep as catch-all for API endpoints (acceptable pattern for top-level handlers)
- **Recommended:** Keep as is - this is a top-level API handler that should catch all unexpected errors

---

#### 1.2 `backend/app/api/channels.py:325`
**Context:** Channel info refresh endpoint (within loop processing channels)
**Current Code:**
```python
except (SQLAlchemyError, IntegrityError) as e:
    # ... database error handling
except Exception as e:
    logger.error(f"Failed to refresh info for {channel.username}: {e}")
    results.append(ChannelInfoUpdate(..., success=False))
```

**Recommendation:**
- Replace with: `(TelegramError, NetworkError, ValueError)`
- Import from: `from telethon.errors import TelegramError, NetworkError`
- **Rationale:** Refreshing channel info involves Telegram API calls which can raise Telegram-specific errors

---

#### 1.3 `backend/app/api/alerts.py:115`
**Context:** Alert creation endpoint
**Current Code:**
```python
except HTTPException:
    raise
except (SQLAlchemyError, IntegrityError) as e:
    # ... database error handling
except Exception as e:
    logger.error(f"Unexpected error creating alert: {e}")
    raise HTTPException(status_code=500, detail="ALERT_CREATE_ERROR")
```

**Recommendation:**
- **Keep as is** - top-level API handler should catch all unexpected errors
- Consider adding: `ValueError` and `TypeError` if input validation happens here
- **Preferred:** Keep as catch-all for API safety

---

#### 1.4 `backend/app/api/messages.py:66`
**Context:** Cursor decoding utility function
**Current Code:**
```python
def _decode_cursor(cursor: str) -> tuple[datetime, UUID]:
    try:
        decoded = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
        # ... parsing logic
        return published_at, message_id
    except Exception as exc:
        logger.warning(f"Failed to decode cursor: {type(exc).__name__}: {exc}")
        raise HTTPException(status_code=400, detail="Invalid cursor format")
```

**Recommendation:**
- Replace with: `(ValueError, binascii.Error, UnicodeDecodeError)`
- Import: `import binascii`
- **Rationale:** Specific errors from base64 decoding, string parsing, UUID/datetime conversion

---

#### 1.5 `backend/app/api/messages.py:205`
**Context:** Message search endpoint
**Current Code:**
```python
except HTTPException:
    raise
except (SQLAlchemyError, IntegrityError) as e:
    # ... database error handling
except Exception as e:
    logger.error(f"Unexpected error searching messages: {e}")
    raise HTTPException(status_code=500, detail="MESSAGE_SEARCH_ERROR")
```

**Recommendation:**
- **Keep as is** - top-level API handler should catch all unexpected errors for safety
- **Rationale:** Already catches specific DB errors; catch-all is acceptable for API endpoints

---

#### 1.6 `backend/app/api/collections.py:315`
**Context:** Collection creation endpoint
**Current Code:**
```python
except HTTPException:
    raise
except (SQLAlchemyError, IntegrityError) as e:
    # ... database error handling
except Exception as e:
    logger.error(f"Unexpected error creating collection: {e}")
    raise HTTPException(status_code=500, detail="COLLECTION_CREATE_ERROR")
```

**Recommendation:**
- **Keep as is** - top-level API handler should catch all unexpected errors
- **Rationale:** Follows established pattern for API endpoints; catch-all is safe here

---

### 2. Services

#### 2.1 `backend/app/services/channel_utils.py:520`
**Context:** Channel add utility function
**Current Code:**
```python
except (TelegramError, NetworkError, ValueError, HTTPException) as e:
    # ... Telegram/network error handling
except (SQLAlchemyError, IntegrityError) as e:
    # ... database error handling
except Exception as e:
    logger.error(f"Unexpected error adding channel: {e}")
    if error_mode == "raise":
        raise HTTPException(status_code=500, detail="CHANNEL_ADD_ERROR")
```

**Recommendation:**
- Replace with: `(OSError, RuntimeError, AttributeError)`
- **Rationale:** Catches system errors, runtime errors, and attribute access errors that might occur during channel operations
- **Alternative:** Keep as catch-all since this is a critical service function that should never crash

---

#### 2.2 `backend/app/services/llm_translator.py:631`
**Context:** Fallback translation after primary and Google Translate fail
**Current Code:**
```python
except (OpenAIError, httpx.HTTPError, Exception) as e:
    # Primary provider failed - fall back to Google Translate
    try:
        translated_text = await self._translate_with_google(text, source_lang, target_lang)
    except Exception as fallback_error:
        # All translation methods failed - return original text
        logger.error(f"Fallback translation failed (All methods): {fallback_error}")
        return text, source_lang, priority
```

**Recommendation:**
- Replace with: `(TranslationError, LangDetectException, httpx.HTTPError, ValueError)`
- Import: `from deep_translator.exceptions import TranslationError` (if available)
- **Rationale:** Google Translate via deep_translator can raise specific translation errors
- **Alternative:** Keep as catch-all since this is the final fallback and returns gracefully

---

#### 2.3 `backend/app/services/message_media_service.py:100`
**Context:** Fetching media from Telegram
**Current Code:**
```python
except HTTPException:
    raise
except Exception as e:
    logger.exception(f"Failed to fetch media for message {message_id}: {e}")
    raise HTTPException(status_code=502, detail="Failed to fetch media from Telegram")
```

**Recommendation:**
- Replace with: `(TelegramError, NetworkError, OSError, ValueError)`
- Import: `from telethon.errors import TelegramError, NetworkError`
- **Rationale:** Telegram media operations can raise Telegram-specific and network errors

---

#### 2.4 `backend/app/services/auth_rate_limiter.py:61`
**Context:** Rate limiting with Redis
**Current Code:**
```python
except HTTPException:
    raise
except RedisError as e:
    logger.error(f"Redis connection error - rate limiter unavailable: {e}")
    raise HTTPException(status_code=503, detail="Rate limiter unavailable")
except Exception as e:
    logger.error(f"Unexpected error in rate limiter: {e}")
    raise HTTPException(status_code=503, detail="Rate limiter unavailable")
```

**Recommendation:**
- Replace with: `(ValueError, TypeError, AttributeError)`
- **Rationale:** Catches data validation and attribute errors
- **Alternative:** Keep as catch-all for critical service (rate limiter should never crash)
- **Preferred:** Keep as is - rate limiter is critical infrastructure

---

### 3. Auth & Email

#### 3.1 `backend/app/auth/users.py:150`
**Context:** Creating async task to send verification email
**Current Code:**
```python
try:
    asyncio.create_task(email_service.send_verification(user.email, token))
except RuntimeError as e:
    logger.error(f"Failed to create verification email task (event loop error): {e}")
except Exception as e:
    logger.error(f"Failed to create verification email task: {e}")
```

**Recommendation:**
- Replace with: `(asyncio.CancelledError, OSError, ValueError)`
- Import: `import asyncio`
- **Rationale:** Task creation can fail due to event loop issues, cancellation, or OS errors
- **Alternative:** Keep as catch-all since email sending is non-critical (already handled gracefully)

---

#### 3.2 `backend/app/auth/users.py:178`
**Context:** Creating async task to send password reset email
**Current Code:**
```python
try:
    asyncio.create_task(email_service.send_password_reset(user.email, token))
except RuntimeError as e:
    logger.error(f"Failed to create password reset email task (event loop error): {e}")
except Exception as e:
    logger.error(f"Failed to create password reset email task: {e}")
```

**Recommendation:**
- Same as 3.1: Replace with `(asyncio.CancelledError, OSError, ValueError)`
- **Rationale:** Same context as verification email

---

#### 3.3 `backend/app/auth/users.py:201`
**Context:** Creating async task to send verification email (request verify)
**Current Code:**
```python
try:
    asyncio.create_task(email_service.send_verification(user.email, token))
except RuntimeError as e:
    logger.error(f"Failed to create verification email task (event loop error): {e}")
except Exception as e:
    logger.error(f"Failed to create verification email task: {e}")
```

**Recommendation:**
- Same as 3.1 and 3.2: Replace with `(asyncio.CancelledError, OSError, ValueError)`
- **Rationale:** Same context as other email task creation

---

### 4. Main Application

#### 4.1 `backend/app/main.py:170`
**Context:** Health check endpoint
**Current Code:**
```python
try:
    engine = get_engine()
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "healthy", "database": "connected"}
except SQLAlchemyError as e:
    logger.warning(f"Health check failed: {e}")
    return JSONResponse(status_code=503, content={...})
except Exception as e:
    logger.warning(f"Health check failed with unexpected error: {e}")
    return JSONResponse(status_code=503, content={...})
```

**Recommendation:**
- Replace with: `(OSError, ConnectionError, TimeoutError)`
- **Rationale:** Health checks can fail due to network/connection issues
- **Alternative:** Keep as catch-all - health checks should never raise exceptions
- **Preferred:** Keep as is for health check safety

---

### 5. CLI Tools

#### 5.1 `backend/app/cli/telegram_setup.py:156`
**Context:** Telegram authentication setup CLI
**Current Code:**
```python
except (RPCError, FloodWaitError) as e:
    print(f"\nTelegram error: {e}")
    sys.exit(1)
except OSError as e:
    print(f"\nNetwork error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\nUnexpected error: {e}")
    sys.exit(1)
```

**Recommendation:**
- Replace with: `(ValueError, KeyError, AttributeError)`
- **Rationale:** CLI can encounter config errors, missing environment variables
- **Alternative:** Keep as catch-all for CLI tools (acceptable pattern)
- **Preferred:** Keep as is - CLI tools should handle all errors gracefully

---

#### 5.2 `backend/verify_gin_index.py:123`
**Context:** Database verification script (main check function)
**Current Code:**
```python
try:
    # ... verification logic
except Exception as e:
    print(f"❌ ERROR: {e}")
    traceback.print_exc()
    return False
```

**Recommendation:**
- Replace with: `(SQLAlchemyError, psycopg2.Error, OSError)`
- Import: `import psycopg2`
- **Rationale:** Verification script primarily does database operations
- **Alternative:** Keep as catch-all for verification scripts
- **Preferred:** Keep as is with comment

---

#### 5.3 `backend/verify_gin_index.py:144`
**Context:** Database verification script (main entry point)
**Current Code:**
```python
async def main():
    try:
        success = await check_index_usage()
        # ... handle success
    except Exception as e:
        print(f"❌ Verification FAILED: {e}")
        traceback.print_exc()
        sys.exit(1)
```

**Recommendation:**
- **Keep as is** - Top-level main() in CLI scripts should catch all exceptions
- Add comment: `# Catch-all for CLI tool - all errors should be logged and exit gracefully`
- **Rationale:** CLI tools need bulletproof error handling

---

### 6. Utilities

#### 6.1 `backend/app/utils/retry.py:70`
**Context:** Retry decorator - non-retryable errors
**Current Code:**
```python
except Exception as e:
    # Intentional catch-all for non-retryable errors (anything not in retryable_exceptions)
    # Log the error type for debugging, then re-raise immediately to fail fast
    logger.error(f"Non-retryable error in {func.__name__}: {type(e).__name__}: {e}")
    raise
```

**Recommendation:**
- ✅ **KEEP AS IS - INTENTIONAL CATCH-ALL**
- The comment clearly explains this is intentional for catching non-retryable errors
- The exception is immediately re-raised (fail fast)
- **Action:** No change needed - already properly documented

---

## Recommended Action Plan

### Phase 1: High Priority - Service Layer (4 files)
These have clear specific exceptions and should be replaced:

1. ✅ `message_media_service.py:100` → `(TelegramError, NetworkError, OSError, ValueError)`
2. ✅ `llm_translator.py:631` → `(httpx.HTTPError, ValueError, RuntimeError)` or keep as is
3. ✅ `channel_utils.py:520` → Keep as is (already well-handled)
4. ⚠️ `auth_rate_limiter.py:61` → Keep as is (critical infrastructure)

### Phase 2: Medium Priority - API Endpoints (3 files)
Consider replacing or documenting as intentional:

1. ✅ `messages.py:66` → `(ValueError, binascii.Error, UnicodeDecodeError)`
2. ⚠️ `auth.py:85` → Keep as is (top-level handler)
3. ⚠️ `alerts.py:115` → Keep as is (top-level handler)
4. ⚠️ `messages.py:205` → Keep as is (top-level handler)
5. ⚠️ `collections.py:315` → Keep as is (top-level handler)
6. ✅ `channels.py:325` → `(TelegramError, NetworkError, ValueError)`

### Phase 3: Low Priority - Auth/Email (1 file, 3 instances)
Non-critical email operations:

1. ✅ `users.py:150, 178, 201` → `(asyncio.CancelledError, OSError, ValueError)` or keep as is

### Phase 4: CLI Tools (2 files, 3 instances)
CLI tools typically keep catch-all:

1. ⚠️ `telegram_setup.py:156` → Keep as is with comment
2. ⚠️ `verify_gin_index.py:123, 144` → Keep as is with comment

### Phase 5: Main App (1 file)
1. ⚠️ `main.py:170` → Keep as is (health check should never crash)

---

## Summary Statistics

- **Total instances:** 18
- **Keep as intentional catch-all:** 11 (API endpoints, health check, CLI tools, rate limiter)
- **Replace with specific exceptions:** 7 (services, utilities)
- **Already properly documented:** 1 (retry.py)

---

## Import Additions Required

### For Telegram errors:
```python
from telethon.errors import TelegramError, NetworkError
```

### For asyncio errors:
```python
import asyncio  # Already imported in most files
# Use: asyncio.CancelledError
```

### For binary/encoding errors:
```python
import binascii  # For base64 decoding errors
# Use: binascii.Error, UnicodeDecodeError, ValueError
```

### For database errors:
```python
import psycopg2  # For direct PostgreSQL errors (verify scripts)
# Or use existing SQLAlchemyError
```

---

## Notes

1. **API Endpoints Pattern:** The pattern of having a final `except Exception` in API route handlers is **acceptable** and commonly recommended for production APIs. It ensures:
   - No unhandled exceptions crash the API
   - All errors are logged
   - Users get meaningful HTTP error responses
   - The application remains stable

2. **CLI Tools Pattern:** CLI tools (telegram_setup.py, verify_gin_index.py) should keep catch-all exception handlers at the top level to ensure graceful error messages and proper exit codes.

3. **Health Checks:** The health check endpoint (main.py:170) should keep its catch-all to ensure the endpoint never crashes.

4. **Critical Services:** Rate limiters and other critical infrastructure should keep catch-all handlers to prevent service disruption.

5. **Spec Discrepancy:** The spec mentioned 51 instances, but only 18 were found. This suggests significant cleanup has already occurred, or the spec was based on a different codebase state.
