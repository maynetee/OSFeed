#!/bin/bash
set -e

echo "Running database migrations..."

# Run pending migrations (idempotent — safe to re-run)
alembic upgrade head

echo "Migrations complete!"
echo "Starting application..."
exec "$@"
