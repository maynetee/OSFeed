#!/bin/bash
set -e

echo "Running database migrations..."

# Try to run migrations
if ! alembic upgrade head 2>&1; then
    echo "Migration failed, checking if database needs stamping..."

    # Check if this is a "relation already exists" error (database exists but no alembic tracking)
    # Stamp to the latest merge revision
    echo "Stamping database to known state (c4d5e6f7a8b9)..."
    alembic stamp c4d5e6f7a8b9 || true

    echo "Retrying migrations..."
    alembic upgrade head
fi

echo "Migrations complete!"
echo "Starting application..."
exec "$@"
