#!/usr/bin/env python3
import argparse
import asyncio
import os

import asyncpg


def build_postgres_dsn():
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "osfeed_db")
    user = os.getenv("POSTGRES_USER", "osfeed_user")
    password = os.getenv("POSTGRES_PASSWORD", "")
    if password:
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"
    return f"postgresql://{user}@{host}:{port}/{db}"


async def check_postgres(dsn):
    conn = await asyncpg.connect(dsn)
    try:
        value = await conn.fetchval("SELECT 1")
        if value != 1:
            raise RuntimeError("Unexpected SELECT 1 result")
        tables = ["channels", "messages", "summaries", "users"]
        results = {}
        for table in tables:
            results[table] = await conn.fetchval("SELECT to_regclass($1)", f"public.{table}") is not None
    finally:
        await conn.close()

    print("PostgreSQL connection OK.")
    for table, exists in results.items():
        status = "OK" if exists else "MISSING"
        print(f"Table {table}: {status}")


def main():
    parser = argparse.ArgumentParser(description="Check PostgreSQL connectivity and schema.")
    parser.add_argument("--postgres-dsn", default=build_postgres_dsn(), help="PostgreSQL DSN.")
    args = parser.parse_args()
    asyncio.run(check_postgres(args.postgres_dsn))


if __name__ == "__main__":
    main()
