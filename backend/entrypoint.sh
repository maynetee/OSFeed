#!/bin/bash
set -e

echo "Running database migrations..."

# Stamp to last known safe base and re-run idempotent migrations
# This ensures any missing columns/tables are created
alembic stamp c4d5e6f7a8b9
alembic upgrade head

echo "Migrations complete!"
echo "Starting application..."
exec "$@"
