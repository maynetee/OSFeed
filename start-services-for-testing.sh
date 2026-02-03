#!/bin/bash

# Start services for manual browser testing
# Cookie-based authentication implementation

set -e

echo "======================================="
echo "Starting Services for Manual Testing"
echo "Cookie-Based Authentication"
echo "======================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "Error: Must run from project root directory"
    exit 1
fi

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo -e "${YELLOW}Warning: Port $port is already in use${NC}"
        return 1
    fi
    return 0
}

# Check ports
echo "Checking ports..."
check_port 8000 || echo "  Backend port 8000 is occupied (this is OK if backend is already running)"
check_port 5173 || echo "  Frontend port 5173 is occupied (this is OK if frontend is already running)"
echo ""

# Start Backend
echo "======================================="
echo "1. Starting Backend (FastAPI)"
echo "======================================="
echo "  Port: 8000"
echo "  Docs: http://localhost:8000/docs"
echo ""

cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating one...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing backend dependencies..."
    pip install -r requirements.txt
fi

# Start backend in background
echo "Starting backend server..."
echo "Command: uvicorn app.main:app --reload --port 8000"
echo ""
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
echo ""

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Backend failed to start. Check logs."
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done
echo ""

cd ..

# Start Frontend
echo "======================================="
echo "2. Starting Frontend (Vite)"
echo "======================================="
echo "  Port: 5173"
echo "  URL: http://localhost:5173"
echo ""

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}node_modules not found. Installing dependencies...${NC}"
    npm install
fi

# Start frontend in background
echo "Starting frontend development server..."
echo "Command: npm run dev"
echo ""
npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
echo ""

# Wait for frontend to be ready
echo "Waiting for frontend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:5173 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Frontend failed to start. Check logs."
        kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done
echo ""

cd ..

# Summary
echo "======================================="
echo "✓ Services Started Successfully!"
echo "======================================="
echo ""
echo "Backend:  http://localhost:8000"
echo "          http://localhost:8000/docs (API docs)"
echo "Frontend: http://localhost:5173"
echo ""
echo "Process IDs:"
echo "  Backend:  $BACKEND_PID"
echo "  Frontend: $FRONTEND_PID"
echo ""
echo "To stop services:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo "  Or press Ctrl+C"
echo ""
echo "======================================="
echo "Next Steps:"
echo "======================================="
echo ""
echo "1. Open MANUAL_TESTING_GUIDE.md"
echo "2. Follow the test scenarios"
echo "3. Verify all checklist items"
echo ""
echo "Press Ctrl+C to stop all services when done."
echo ""

# Save PIDs to file for easy cleanup
echo "$BACKEND_PID" > .test-backend.pid
echo "$FRONTEND_PID" > .test-frontend.pid

# Wait for user to stop
wait
