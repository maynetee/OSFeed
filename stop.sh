#!/bin/bash

# OSFeed - Stop Docker services
# Usage:
#   ./stop.sh           -> docker compose stop
#   ./stop.sh --down    -> docker compose down
#   ./stop.sh --wipe    -> docker compose down -v (remove volumes)

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

MODE="stop"
if [ "$1" = "--down" ]; then
    MODE="down"
elif [ "$1" = "--wipe" ]; then
    MODE="wipe"
fi

echo -e "${BLUE}Stopping OSFeed (${MODE})...${NC}"

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
