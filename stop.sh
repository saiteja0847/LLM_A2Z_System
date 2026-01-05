#!/bin/bash

# AI Lab Platform - Stop Script
# Gracefully stops all running servers

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT="8000"
FRONTEND_PORT="5174"

echo "=========================================="
echo "  AI Lab Platform - Stopping Services"
echo "=========================================="
echo ""

# Function to stop process on port
stop_port() {
    local port=$1
    local service=$2

    local pids=$(lsof -ti:$port 2>/dev/null)

    if [ -z "$pids" ]; then
        echo -e "${YELLOW}No $service process found on port $port${NC}"
        return 0
    fi

    echo -e "${YELLOW}Stopping $service (port $port)...${NC}"
    echo "$pids" | xargs kill -TERM 2>/dev/null

    # Wait for graceful shutdown
    local attempts=0
    while [ $attempts -lt 10 ]; do
        if ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo -e "${GREEN}✓ $service stopped${NC}"
            return 0
        fi
        sleep 1
        attempts=$((attempts + 1))
    done

    # Force kill if still running
    echo -e "${YELLOW}Force stopping $service...${NC}"
    echo "$pids" | xargs kill -9 2>/dev/null
    echo -e "${GREEN}✓ $service stopped (forced)${NC}"
}

# Stop backend
stop_port $BACKEND_PORT "Backend"

# Stop frontend
stop_port $FRONTEND_PORT "Frontend"

# Clean up log files
if [ -f "backend.log" ] || [ -f "frontend.log" ]; then
    echo ""
    echo -e "${YELLOW}Log files preserved:${NC}"
    [ -f "backend.log" ] && echo "  - backend.log"
    [ -f "frontend.log" ] && echo "  - frontend.log"
fi

echo ""
echo -e "${GREEN}✓ All services stopped${NC}"
echo ""
