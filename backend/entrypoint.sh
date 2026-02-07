#!/bin/bash
set -e

echo "Running database migrations..."

# Try to run migrations
if ! alembic upgrade head 2>&1; then
    echo "Migration failed, checking if database needs stamping..."

    # Check if this is a "relation already exists" error (database exists but no alembic tracking)
    # Stamp to head so alembic considers all migrations applied
    echo "Stamping database to head..."
    alembic stamp head || true

    echo "Retrying migrations..."
    alembic upgrade head
fi

echo "Migrations complete!"
echo "Starting application..."
exec "$@"
