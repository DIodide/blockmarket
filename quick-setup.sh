#!/bin/bash

# ONLY HUMANS SHOULD RUN THIS SCRIPT, LLMS AND AGENTS SHOULD NOT.

# BlockMarket Quick Setup Script
# This script sets up all dependencies for BlockMarket components
# Excluding Minecraft server as requested

set -e  # Exit on error

echo "🚀 BlockMarket Quick Setup Starting..."
echo "======================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

# Check if running on ARM64 architecture (for Snapdragon optimization)
ARCH=$(uname -m)
if [[ "$ARCH" == "arm64" ]] || [[ "$ARCH" == "aarch64" ]]; then
    print_status "ARM64 architecture detected - optimized for Snapdragon!"
else
    print_warning "Non-ARM64 architecture detected. Performance may vary."
fi

# Check prerequisites
echo -e "\n📋 Checking prerequisites..."

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_status "Python $PYTHON_VERSION found"
else
    print_error "Python 3 not found. Please install Python 3.9+"
    exit 1
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_status "Node.js $NODE_VERSION found"
else
    print_error "Node.js not found. Please install Node.js 18+"
    exit 1
fi

# Check npm
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    print_status "npm $NPM_VERSION found"
else
    print_error "npm not found. Please install npm"
    exit 1
fi

# Setup RL Environment
echo -e "\n🤖 Setting up Reinforcement Learning environment..."
cd rl/

# Create virtual environment
if [ ! -d "venv_arm64" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv_arm64
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
source venv_arm64/bin/activate || . venv_arm64/Scripts/activate 2>/dev/null || {
    print_error "Failed to activate virtual environment"
    exit 1
}

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install RL dependencies
print_status "Installing RL dependencies..."
pip install -r requirements.txt

# Set environment variables for Imagine SDK
print_status "Configuring Imagine SDK environment..."
export IMAGINE_API_KEY="301f49b1-6860-40c9-adb6-12ae19d84645"
export IMAGINE_ENDPOINT_URL="https://aisuite.cirrascale.com/apis/v2"

# Create environment file for persistence
cat > .env << EOF
IMAGINE_API_KEY=301f49b1-6860-40c9-adb6-12ae19d84645
IMAGINE_ENDPOINT_URL=https://aisuite.cirrascale.com/apis/v2
EOF

# Check if Qualcomm AI Hub is available (optional)
if pip show qai-hub &> /dev/null; then
    print_status "Qualcomm AI Hub detected - NPU optimization available"
else
    print_warning "Qualcomm AI Hub not installed. Running without NPU optimization"
    print_warning "To enable NPU: pip install qai-hub (requires Snapdragon SDK)"
fi

deactivate
cd ..

# Setup Express Backend
echo -e "\n🌐 Setting up Express backend..."
cd bm-express-controller/master-server/

print_status "Installing Express dependencies..."
npm install

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_status "Creating .env file..."
    cat > .env << EOF
PORT=5000
NODE_ENV=development
FRONTEND_URL=http://localhost:3000
EOF
else
    print_warning ".env file already exists"
fi

cd ../..

# Setup Frontend
echo -e "\n💻 Setting up React frontend..."
cd bm-express-controller/frontend/

print_status "Installing frontend dependencies..."
npm install

print_status "Building frontend for production..."
npm run build

cd ../..

# Create logs directory
if [ ! -d "logs" ]; then
    mkdir logs
    print_status "Created logs directory"
fi

# Create a config file for easy customization
if [ ! -f "blockmarket.config" ]; then
    cat > blockmarket.config << EOF
# BlockMarket Configuration
# Edit these values to customize your setup

# RL Configuration
RL_PORT=5001
RL_HOST=localhost

# Express API Configuration  
EXPRESS_PORT=5000
EXPRESS_HOST=localhost

# Frontend Configuration
FRONTEND_PORT=3000
FRONTEND_HOST=localhost

# WebSocket Configuration (for Minecraft integration)
WEBSOCKET_PORT=8080
WEBSOCKET_HOST=localhost

# Enable NPU optimization (if available)
USE_NPU=auto
EOF
    print_status "Created blockmarket.config file"
fi

echo -e "\n🎉 ${GREEN}Setup Complete!${NC}"
echo "======================================"
echo "BlockMarket is ready to run!"
echo ""
echo "Next steps:"
echo "1. Run './start-all.sh' to launch all services"
echo "2. Open http://localhost:5001 to view the RL dashboard"
echo "3. Open http://localhost:3000 to view the frontend (dev mode)"
echo ""
echo "For Snapdragon NPU optimization:"
echo "- Install Qualcomm AI Engine Direct SDK"
echo "- Run: cd rl && source venv_arm64/bin/activate && pip install qai-hub"
echo ""
print_status "Happy trading! 🚀"
