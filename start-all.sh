#!/bin/bash

# BlockMarket Start All Services Script
# Launches all BlockMarket services (excluding Minecraft)

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Load configuration if exists
if [ -f "blockmarket.config" ]; then
    source blockmarket.config
    print_status "Loaded configuration from blockmarket.config"
else
    print_warning "No blockmarket.config found, using defaults"
    # Set defaults
    RL_PORT=5001
    EXPRESS_PORT=5000
    FRONTEND_PORT=3000
    WEBSOCKET_PORT=8080
fi

echo "🚀 Starting BlockMarket Services..."
echo "======================================"

# Function to kill process on port
kill_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Killing existing process on port $port"
        lsof -Pi :$port -sTCP:LISTEN -t | xargs kill -9 2>/dev/null || true
    fi
}

# Clean up function
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    
    # Kill all background processes started by this script
    jobs -p | xargs -r kill 2>/dev/null || true
    
    # Kill processes on specific ports
    kill_port $RL_PORT
    kill_port $EXPRESS_PORT
    kill_port $FRONTEND_PORT
    
    print_status "All services stopped"
    exit 0
}

# Set up trap to clean up on exit
trap cleanup EXIT INT TERM

# Create logs directory if it doesn't exist
mkdir -p logs

# Check if services are already running and kill them
print_info "Checking for existing services..."
kill_port $RL_PORT
kill_port $EXPRESS_PORT
kill_port $FRONTEND_PORT

# Start RL Training Environment
echo -e "\n🤖 Starting RL Training Environment..."
cd rl/

# Activate virtual environment
if [ -d "venv_arm64" ]; then
    source venv_arm64/bin/activate || . venv_arm64/Scripts/activate 2>/dev/null
else
    print_error "Virtual environment not found. Run ./quick-setup.sh first"
    exit 1
fi

# Start the RL web server
print_status "Starting RL visualization server on port $RL_PORT..."
python web_server.py --port $RL_PORT > ../logs/rl_server.log 2>&1 &
RL_PID=$!

# Start the RL training in background
print_status "Starting RL training loop..."
python training.py > ../logs/rl_training.log 2>&1 &
TRAINING_PID=$!

deactivate
cd ..

# Start Express Backend
echo -e "\n🌐 Starting Express Backend..."
cd bm-express-controller/master-server/

print_status "Starting Express API server on port $EXPRESS_PORT..."
npm start > ../../logs/express_server.log 2>&1 &
EXPRESS_PID=$!

cd ../..

# Start Frontend (Development Server)
echo -e "\n💻 Starting React Frontend..."
cd bm-express-controller/frontend/

print_status "Starting React development server on port $FRONTEND_PORT..."
npm run dev > ../../logs/frontend.log 2>&1 &
FRONTEND_PID=$!

cd ../..

# Wait for services to start
echo -e "\n⏳ Waiting for services to initialize..."
sleep 5

# Check if services are running
check_service() {
    local port=$1
    local name=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_status "$name is running on port $port"
        return 0
    else
        print_error "$name failed to start on port $port"
        return 1
    fi
}

echo -e "\n📊 Service Status:"
echo "======================================"
check_service $RL_PORT "RL Visualization Server"
check_service $EXPRESS_PORT "Express API Server"
check_service $FRONTEND_PORT "React Frontend"

# Display access URLs
echo -e "\n🌟 ${GREEN}All services started successfully!${NC}"
echo "======================================"
echo "Access your services at:"
echo ""
echo "📊 RL Dashboard:        http://localhost:$RL_PORT"
echo "🔧 Express API:         http://localhost:$EXPRESS_PORT"
echo "💻 React Frontend:      http://localhost:$FRONTEND_PORT"
echo "📡 API Health Check:    http://localhost:$EXPRESS_PORT/health"
echo ""
echo "📝 Logs are available in the 'logs' directory:"
echo "   - RL Server:     logs/rl_server.log"
echo "   - RL Training:   logs/rl_training.log"
echo "   - Express API:   logs/express_server.log"
echo "   - Frontend:      logs/frontend.log"
echo ""
echo "🛑 Press Ctrl+C to stop all services"
echo ""

# Monitor services
print_info "Monitoring services... (Press Ctrl+C to stop)"

# Function to check if a process is still running
check_process() {
    if ! kill -0 $1 2>/dev/null; then
        return 1
    fi
    return 0
}

# Keep the script running and monitor services
while true; do
    sleep 10
    
    # Check if critical services are still running
    if ! check_process $RL_PID; then
        print_error "RL server crashed! Check logs/rl_server.log"
        break
    fi
    
    if ! check_process $EXPRESS_PID; then
        print_error "Express server crashed! Check logs/express_server.log"
        break
    fi
    
    if ! check_process $FRONTEND_PID; then
        print_error "Frontend server crashed! Check logs/frontend.log"
        break
    fi
done

print_error "One or more services failed. Shutting down..."
cleanup
