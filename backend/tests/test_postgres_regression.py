import os
import pytest
import asyncpg


def build_postgres_dsn() -> str:
    if os.getenv("POSTGRES_DSN"):
        return os.environ["POSTGRES_DSN"]
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "telescope_db")
    user = os.getenv("POSTGRES_USER", "telescope_user")
    password = os.getenv("POSTGRES_PASSWORD", "")
    if password:
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"
    return f"postgresql://{user}@{host}:{port}/{db}"


@pytest.mark.asyncio
async def test_postgres_schema_regression():
    if not os.getenv("POSTGRES_HOST") and not os.getenv("POSTGRES_DSN"):
        pytest.skip("PostgreSQL environment not configured")

    dsn = build_postgres_dsn()
    conn = await asyncpg.connect(dsn)
    try:
        value = await conn.fetchval("SELECT 1")
        assert value == 1

        tables = [
            "users",
            "channels",
            "messages",
            "summaries",
            "audit_logs",
            "collections",
            "api_usages",
        ]
        for table in tables:
            exists = await conn.fetchval("SELECT to_regclass($1)", f"public.{table}") is not None
            assert exists, f"Missing table: {table}"

        columns = await conn.fetch(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'users'
            """
        )
        user_columns = {row["column_name"] for row in columns}
        assert "refresh_token_hash" in user_columns
        assert "refresh_token_expires_at" in user_columns
    finally:
        await conn.close()
