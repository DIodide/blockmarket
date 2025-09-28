#!/bin/bash

# BlockMarket Stop All Services Script
# Stops all running BlockMarket services

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

echo "🛑 Stopping BlockMarket Services..."
echo "======================================"

# Function to kill process on port
kill_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Stopping $service on port $port..."
        lsof -Pi :$port -sTCP:LISTEN -t | xargs kill -9 2>/dev/null || true
        print_status "$service stopped"
    else
        print_status "$service not running on port $port"
    fi
}

# Load configuration if exists
if [ -f "blockmarket.config" ]; then
    source blockmarket.config
else
    # Set defaults
    RL_PORT=5001
    EXPRESS_PORT=5000
    FRONTEND_PORT=3000
    WEBSOCKET_PORT=8080
fi

# Kill services
kill_port $RL_PORT "RL Visualization Server"
kill_port $EXPRESS_PORT "Express API Server"
kill_port $FRONTEND_PORT "React Frontend"

# Also kill any python training processes
pkill -f "python.*training.py" 2>/dev/null || true
pkill -f "python.*web_server.py" 2>/dev/null || true

echo ""
print_status "All BlockMarket services stopped"
echo "======================================"
