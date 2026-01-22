#!/bin/bash

# OSFeed - Docker Server
# Usage: ./start.sh           -> Production mode (with Caddy HTTPS) - DEFAULT
#        ./start.sh --dev     -> Development mode

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Production mode by default
PROD_MODE=true
if [ "$1" = "--dev" ]; then
    PROD_MODE=false
fi

if [ "$PROD_MODE" = true ]; then
    echo -e "${BLUE}Starting OSFeed (Production)...${NC}"
else
    echo -e "${BLUE}Starting OSFeed (Development)...${NC}"
fi

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
if [ "$PROD_MODE" = true ]; then
    $COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml up -d --build
else
    $COMPOSE_CMD up -d --build
fi

# Set compose command with files for exec operations
if [ "$PROD_MODE" = true ]; then
    COMPOSE_EXEC="$COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml"
else
    COMPOSE_EXEC="$COMPOSE_CMD"
fi

# Wait for backend to be ready
echo -e "${BLUE}Waiting for backend to be ready...${NC}"
sleep 5
until $COMPOSE_EXEC exec -T backend python -c "import socket; s=socket.socket(); s.connect(('localhost',8000)); s.close()" 2>/dev/null; do
  echo -n "."
  sleep 2
done
echo ""

# Run migrations
echo -e "${BLUE}Running migrations...${NC}"
$COMPOSE_EXEC exec -T backend alembic upgrade head

if [ "$MIGRATE_SQLITE" = "1" ] && [ -f "$ROOT_DIR/data/osfeed.db" ]; then
    echo -e "${BLUE}Migrating SQLite data into PostgreSQL...${NC}"
    $COMPOSE_EXEC exec -T backend python scripts/migrate_sqlite_to_postgres.py
fi

echo -e "\n${GREEN}OSFeed is running!${NC}"
if [ "$PROD_MODE" = true ]; then
    echo -e "  URL:   https://osfeed.com"
    echo -e "  IP:    http://135.125.100.103"
    echo -e "  Docs:  https://osfeed.com/docs"
    echo -e "\nTo stop: ./stop.sh"
    echo -e "To view logs: $COMPOSE_EXEC logs -f"
else
    echo -e "  Frontend: http://localhost:5173"
    echo -e "  Backend:  http://localhost:8000"
    echo -e "  Docs:     http://localhost:8000/docs"
    echo -e "\nTo stop: ./stop.sh --dev"
    echo -e "To view logs: $COMPOSE_CMD logs -f"
fi
