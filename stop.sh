#!/bin/bash

# OSFeed - Stop Docker services
# Usage:
#   ./stop.sh                  -> docker compose stop (prod) - DEFAULT
#   ./stop.sh --dev            -> docker compose stop (dev)
#   ./stop.sh --down           -> docker compose down (prod)
#   ./stop.sh --dev --down     -> docker compose down (dev)
#   ./stop.sh --wipe           -> docker compose down -v (remove volumes)
#   ./stop.sh --dev --wipe     -> docker compose down -v (dev, remove volumes)

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

# Parse arguments - Production mode by default
PROD_MODE=true
MODE="stop"
for arg in "$@"; do
    case $arg in
        --dev)
            PROD_MODE=false
            ;;
        --down)
            MODE="down"
            ;;
        --wipe)
            MODE="wipe"
            ;;
    esac
done

if [ "$PROD_MODE" = true ]; then
    echo -e "${BLUE}Stopping OSFeed Production (${MODE})...${NC}"
else
    echo -e "${BLUE}Stopping OSFeed Development (${MODE})...${NC}"
fi

# Check for docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: docker is required but not found.${NC}"
    exit 1
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

# Add production files if in prod mode
if [ "$PROD_MODE" = true ]; then
    COMPOSE_CMD="$COMPOSE_CMD -f docker-compose.yml -f docker-compose.prod.yml"
fi

if [ "$MODE" = "down" ]; then
    echo -e "${BLUE}Bringing Docker services down...${NC}"
    $COMPOSE_CMD down --remove-orphans
elif [ "$MODE" = "wipe" ]; then
    echo -e "${BLUE}Bringing Docker services down (with volumes)...${NC}"
    $COMPOSE_CMD down -v --remove-orphans
else
    echo -e "${BLUE}Stopping Docker services...${NC}"
    $COMPOSE_CMD stop
fi

echo -e "${GREEN}OSFeed stopped.${NC}"
