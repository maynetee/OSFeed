#!/bin/bash
# Frontend CSP Verification Script
# This script verifies that the frontend application works correctly without 'unsafe-eval' in CSP

set -e

echo "=========================================="
echo "Frontend CSP Verification Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "Checking prerequisites..."

# Check for npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}✗ npm is not installed${NC}"
    echo "Please install Node.js and npm first"
    exit 1
fi
echo -e "${GREEN}✓ npm is installed${NC}"

# Check for node
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ node is not installed${NC}"
    echo "Please install Node.js first"
    exit 1
fi
echo -e "${GREEN}✓ node is installed ($(node --version))${NC}"

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    echo -e "${RED}✗ frontend directory not found${NC}"
    echo "Please run this script from the project root"
    exit 1
fi
echo -e "${GREEN}✓ frontend directory found${NC}"

echo ""
echo "Installing frontend dependencies..."
cd frontend

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    npm install
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Dependencies already installed${NC}"
fi

echo ""
echo "Starting frontend dev server..."
echo -e "${YELLOW}The server will start on http://localhost:5173${NC}"
echo ""
echo "=========================================="
echo "VERIFICATION INSTRUCTIONS:"
echo "=========================================="
echo ""
echo "1. Open your browser to: http://localhost:5173"
echo ""
echo "2. Open Browser DevTools:"
echo "   - Chrome/Edge: Press F12 or Ctrl+Shift+I"
echo "   - Firefox: Press F12 or Ctrl+Shift+I"
echo ""
echo "3. Go to the Console tab"
echo ""
echo "4. Check for CSP violations:"
echo -e "   ${GREEN}✓ SUCCESS: No CSP errors, app loads correctly${NC}"
echo -e "   ${RED}✗ FAILURE: CSP violation messages in console${NC}"
echo ""
echo "5. Verify in Network tab > Response Headers:"
echo -e "   ${GREEN}✓ Content-Security-Policy contains: script-src 'self' 'unsafe-inline'${NC}"
echo -e "   ${RED}✗ Should NOT contain: 'unsafe-eval'${NC}"
echo ""
echo "6. Press Ctrl+C to stop the server when done"
echo ""
echo "=========================================="
echo ""

# Start the dev server
npm run dev
