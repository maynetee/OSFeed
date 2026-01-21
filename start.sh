#!/bin/bash

# OSFeed - Docker Development Server
# Usage: ./start.sh

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}Starting OSFeed (Docker Only)...${NC}"

# Check dependencies
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: docker is required but not found.${NC}"
    exit 1
fi

# Ensure .env exists
if [ ! -f "$ROOT_DIR/.env" ]; then
    echo -e "${BLUE}No .env found, copying from .env.example...${NC}"
    cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
    echo -e "${BLUE}Please review .env values.${NC}"
fi

# Determine compose command
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo -e "${RED}Docker Compose not found.${NC}"
    exit 1
fi

# Start all services
echo -e "${BLUE}Starting services...${NC}"
$COMPOSE_CMD up -d --build

# Wait for backend to be ready
echo -e "${BLUE}Waiting for backend to be ready...${NC}"
# Simple sleep loop or wait for port
until $COMPOSE_CMD exec -T backend nc -z localhost 8000; do
  echo -n "."
  sleep 1
done
echo ""

# Run migrations
echo -e "${BLUE}Running migrations...${NC}"
$COMPOSE_CMD exec -T backend alembic upgrade head

if [ "$MIGRATE_SQLITE" = "1" ] && [ -f "$ROOT_DIR/data/osfeed.db" ]; then
    echo -e "${BLUE}Migrating SQLite data into PostgreSQL...${NC}"
    $COMPOSE_CMD exec -T backend python scripts/migrate_sqlite_to_postgres.py
fi

echo -e "\n${GREEN}OSFeed is running!${NC}"
echo -e "  Frontend: http://localhost:5173"
echo -e "  Backend:  http://localhost:8000"
echo -e "  Docs:     http://localhost:8000/docs"
echo -e "\nTo stop: ./stop.sh"
echo -e "To view logs: $COMPOSE_CMD logs -f"
