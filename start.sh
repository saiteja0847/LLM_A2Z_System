#!/bin/bash

# AI Lab Platform - Unified Launch Script
# Starts both backend and frontend servers with health checks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_HOST="localhost"
BACKEND_PORT="8000"
FRONTEND_PORT="5174"
BACKEND_URL="http://${BACKEND_HOST}:${BACKEND_PORT}"
FRONTEND_URL="http://localhost:${FRONTEND_PORT}"

# PID files
BACKEND_PID=""
FRONTEND_PID=""

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Shutting down servers...${NC}"

    if [ ! -z "$BACKEND_PID" ]; then
        echo "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
        # Wait up to 5 seconds for graceful shutdown
        for i in {1..5}; do
            if ! kill -0 $BACKEND_PID 2>/dev/null; then
                break
            fi
            sleep 1
        done
        # Force kill if still running
        if kill -0 $BACKEND_PID 2>/dev/null; then
            echo "Force killing backend..."
            kill -9 $BACKEND_PID 2>/dev/null || true
        fi
    fi

    if [ ! -z "$FRONTEND_PID" ]; then
        echo "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
        # Wait up to 3 seconds for graceful shutdown
        for i in {1..3}; do
            if ! kill -0 $FRONTEND_PID 2>/dev/null; then
                break
            fi
            sleep 1
        done
        # Force kill if still running
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            echo "Force killing frontend..."
            kill -9 $FRONTEND_PID 2>/dev/null || true
        fi
    fi

    echo -e "${GREEN}✓ Servers stopped${NC}"
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM

# Check if ports are available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo -e "${RED}✗ Port $port is already in use${NC}"
        echo "  Please stop the process using this port and try again."
        echo "  Run: lsof -ti:$port | xargs kill -9"
        echo "  Or use: ./start.sh --clear-ports"
        exit 1
    fi
}

# Force clear ports if requested
clear_ports() {
    echo -e "${YELLOW}Clearing ports...${NC}"

    for port in $BACKEND_PORT $FRONTEND_PORT; do
        local pid=$(lsof -ti :$port 2>/dev/null)
        if [ ! -z "$pid" ]; then
            echo "  Killing process $pid on port $port..."
            kill -9 $pid 2>/dev/null || true
        fi
    done

    sleep 1
    echo -e "${GREEN}✓ Ports cleared${NC}"
}

# Health check function
wait_for_health() {
    local url=$1
    local service=$2
    local max_attempts=30
    local attempt=0

    echo -e "${BLUE}Waiting for $service to be ready...${NC}"

    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ $service is ready${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done

    echo -e "${RED}✗ $service failed to start within 30 seconds${NC}"
    return 1
}

# Print header
echo "=========================================="
echo "  AI Lab Platform - Starting Services"
echo "=========================================="
echo ""

# Handle command-line arguments
if [ "$1" = "--clear-ports" ]; then
    clear_ports
    echo ""
fi

# Check if we're in the correct directory
if [ ! -f "src/ai_lab/api/app.py" ]; then
    echo -e "${RED}✗ Error: Please run this script from the LLM_A2Z_System directory${NC}"
    exit 1
fi

# Check port availability
echo -e "${BLUE}Checking port availability...${NC}"
check_port $BACKEND_PORT
check_port $FRONTEND_PORT
echo -e "${GREEN}✓ Ports are available${NC}"
echo ""

# Start backend server
echo -e "${BLUE}Starting backend server...${NC}"
cd "$(dirname "$0")"
PYTHONPATH="${PWD}/src:${PYTHONPATH}" python3 -m uvicorn ai_lab.api.app:app --host $BACKEND_HOST --port $BACKEND_PORT > backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"

# Wait for backend health check
if ! wait_for_health "${BACKEND_URL}/health" "Backend API"; then
    echo -e "${RED}Backend logs:${NC}"
    tail -20 backend.log
    cleanup
    exit 1
fi
echo ""

# Start frontend server
echo -e "${BLUE}Starting frontend server...${NC}"
cd web/web
npm run dev > ../../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ../..
echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"

# Wait for frontend to be ready
if ! wait_for_health "${FRONTEND_URL}" "Frontend"; then
    echo -e "${RED}Frontend logs:${NC}"
    tail -20 frontend.log
    cleanup
    exit 1
fi
echo ""

# Print success message with URLs
echo "=========================================="
echo -e "${GREEN}✓ AI Lab Platform is ready!${NC}"
echo "=========================================="
echo ""
echo -e "${BLUE}Access the application:${NC}"
echo -e "  Frontend: ${GREEN}${FRONTEND_URL}${NC}"
echo -e "  Backend:  ${GREEN}${BACKEND_URL}${NC}"
echo -e "  API Docs: ${GREEN}${BACKEND_URL}/docs${NC}"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo -e "  Backend: ./backend.log"
echo -e "  Frontend: ./frontend.log"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all servers${NC}"
echo ""

# Keep script running
while true; do
    # Check if processes are still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${RED}✗ Backend process died unexpectedly${NC}"
        echo -e "${RED}Backend logs:${NC}"
        tail -20 backend.log
        cleanup
        exit 1
    fi

    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${RED}✗ Frontend process died unexpectedly${NC}"
        echo -e "${RED}Frontend logs:${NC}"
        tail -20 frontend.log
        cleanup
        exit 1
    fi

    sleep 5
done
