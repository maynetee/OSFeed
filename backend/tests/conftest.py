import os
import asyncio
import sqlite3
from datetime import datetime, date
from pathlib import Path

import pytest

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
def _dispose_engine() -> None:
    yield
    from app.database import engine
    loop = asyncio.new_event_loop()
    loop.run_until_complete(engine.dispose())
    loop.close()
