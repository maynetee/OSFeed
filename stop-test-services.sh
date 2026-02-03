#!/bin/bash

# Stop test services

echo "Stopping test services..."

# Kill saved PIDs
if [ -f .test-backend.pid ]; then
    BACKEND_PID=$(cat .test-backend.pid)
    echo "Stopping backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null || echo "  Backend already stopped"
    rm .test-backend.pid
fi

if [ -f .test-frontend.pid ]; then
    FRONTEND_PID=$(cat .test-frontend.pid)
    echo "Stopping frontend (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null || echo "  Frontend already stopped"
    rm .test-frontend.pid
fi

# Also kill by port as fallback
echo "Checking for any remaining processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "  Port 8000 clear"
lsof -ti:5173 | xargs kill -9 2>/dev/null || echo "  Port 5173 clear"

echo "✓ All test services stopped"
