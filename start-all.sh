#!/bin/bash

# BlockMarket Start All Services Script
# Simple bare-bones script to start all services in separate terminals

echo "🚀 Starting BlockMarket Services..."

# Detect OS for terminal command
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    TERMINAL_CMD="osascript -e 'tell application \"Terminal\" to do script \"%s\"'"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    # Windows (Git Bash)
    TERMINAL_CMD="start cmd /k \"%s\""
else
    # Linux
    TERMINAL_CMD="gnome-terminal -- bash -c \"%s; exec bash\""
fi

# Start ngrok
echo "Starting ngrok..."
eval "$(printf "$TERMINAL_CMD" "ngrok http 3001")"

# Start Express server
echo "Starting Express server..."
eval "$(printf "$TERMINAL_CMD" "cd ./bm-express-controller/master-server && npm run dev")"

# Start Frontend
echo "Starting Frontend..."
eval "$(printf "$TERMINAL_CMD" "cd ./bm-express-controller/frontend && npm run dev")"

# Start Python unified app
echo "Starting Python unified app..."
eval "$(printf "$TERMINAL_CMD" "cd rl && python main.py --mode unified")"

echo "✅ All services started in separate terminals!"
echo "Services:"
echo "  - ngrok: http://localhost:4040 (tunnel to 3001)"
echo "  - Express: http://localhost:3001"
echo "  - Frontend: http://localhost:3000"
echo "  - Python: http://localhost:8080"
