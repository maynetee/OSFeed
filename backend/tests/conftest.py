import os
import asyncio
import sqlite3
from datetime import datetime, date
from pathlib import Path

import pytest

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("TELEGRAM_API_ID", "123456")
os.environ.setdefault("TELEGRAM_API_HASH", "test_hash")
os.environ.setdefault("TELEGRAM_PHONE", "+10000000000")
os.environ.setdefault("OPENROUTER_API_KEY", "test_openrouter_key")
os.environ.setdefault("OPENAI_API_KEY", "test_openai_key")
os.environ.setdefault("USE_SQLITE", "true")
os.environ.setdefault("SQLITE_URL", "sqlite+aiosqlite:///./data/test.db")
os.environ.setdefault("SCHEDULER_ENABLED", "false")
os.environ.setdefault("API_USAGE_TRACKING_ENABLED", "false")

# Avoid deprecated sqlite3 default datetime adapters in Python 3.12+.
sqlite3.register_adapter(datetime, lambda value: value.isoformat(sep=" "))
sqlite3.register_adapter(date, lambda value: value.isoformat())


@pytest.fixture(scope="session")
def sqlite_db_path() -> Path:
    return Path("data/test.db")


@pytest.fixture(autouse=True, scope="session")
def _ensure_test_db_dir(sqlite_db_path: Path) -> None:
    sqlite_db_path.parent.mkdir(parents=True, exist_ok=True)
    if sqlite_db_path.exists():
        sqlite_db_path.unlink()


@pytest.fixture(autouse=True, scope="session")
def _override_rate_limiters() -> None:
    """Disable auth rate limiters in tests when Redis is not available."""
    from app.config import get_settings

    settings = get_settings()
    if not settings.redis_url:
        from app.main import app
        from app.services.auth_rate_limiter import (
            rate_limit_forgot_password,
            rate_limit_request_verify,
            rate_limit_register,
            rate_limit_login,
        )

        async def _noop():
            pass

        app.dependency_overrides[rate_limit_forgot_password] = _noop
        app.dependency_overrides[rate_limit_request_verify] = _noop
        app.dependency_overrides[rate_limit_register] = _noop
        app.dependency_overrides[rate_limit_login] = _noop

    yield

    if not settings.redis_url:
        from app.main import app

        app.dependency_overrides.pop(rate_limit_forgot_password, None)
        app.dependency_overrides.pop(rate_limit_request_verify, None)
        app.dependency_overrides.pop(rate_limit_register, None)
        app.dependency_overrides.pop(rate_limit_login, None)


@pytest.fixture(autouse=True, scope="session")
def _dispose_engine() -> None:
    yield
    from app.database import get_engine
    engine = get_engine()
    if engine is not None:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(engine.dispose())
        loop.close()
