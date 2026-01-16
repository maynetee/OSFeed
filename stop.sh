#!/bin/bash

# TeleScope - Stop local development services
# Usage:
#   ./stop.sh           -> stop processes + docker compose stop
#   ./stop.sh --down    -> docker compose down + remove standalone containers
#   ./stop.sh --wipe    -> docker compose down -v + remove standalone containers

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m'

MODE="stop"
if [ "$1" = "--down" ]; then
    MODE="down"
elif [ "$1" = "--wipe" ]; then
    MODE="wipe"
fi

echo -e "${BLUE}Stopping TeleScope (${MODE})...${NC}"

kill_by_port() {
    local port="$1"
    if command -v lsof &> /dev/null; then
        local pids
        pids=$(lsof -ti "tcp:${port}" || true)
        if [ -n "$pids" ]; then
            echo -e "${YELLOW}Stopping process(es) on port ${port}...${NC}"
            kill -TERM $pids 2>/dev/null || true
            sleep 1
            kill -KILL $pids 2>/dev/null || true
        fi
    fi
}

kill_by_pattern() {
    local pattern="$1"
    local pids
    pids=$(pgrep -f "$pattern" || true)
    if [ -n "$pids" ]; then
        echo -e "${YELLOW}Stopping ${pattern}...${NC}"
        kill -TERM $pids 2>/dev/null || true
        sleep 1
        kill -KILL $pids 2>/dev/null || true
    fi
}

# Stop backend/frontend processes (best-effort)
kill_by_port 8000
kill_by_port 5173
kill_by_port 6379
kill_by_pattern "uvicorn app.main:app"
kill_by_pattern "npm run dev"
kill_by_pattern "vite"

# Stop Docker services
if command -v docker &> /dev/null; then
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    elif command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD=""
    fi
    if [ -n "$COMPOSE_CMD" ]; then
        if [ "$MODE" = "down" ]; then
            echo -e "${BLUE}Bringing Docker services down...${NC}"
            (cd "$ROOT_DIR" && $COMPOSE_CMD down --remove-orphans) || true
        elif [ "$MODE" = "wipe" ]; then
            echo -e "${BLUE}Bringing Docker services down (with volumes)...${NC}"
            (cd "$ROOT_DIR" && $COMPOSE_CMD down -v --remove-orphans) || true
        else
            echo -e "${BLUE}Stopping Docker services...${NC}"
            (cd "$ROOT_DIR" && $COMPOSE_CMD stop) || true
        fi
    fi

    if [ "$MODE" != "stop" ]; then
        if docker ps -a --format '{{.Names}}' | grep -q '^telescope-redis$'; then
            echo -e "${YELLOW}Removing standalone telescope-redis container...${NC}"
            docker rm -f telescope-redis >/dev/null 2>&1 || true
        fi
    fi
fi

echo -e "${GREEN}TeleScope stopped.${NC}"
