#!/bin/bash

# Standalone run script for WatAIOliver
# Handles setup AND running in one script

echo "🚀 Starting WatAIOliver..."

# Kill any existing processes
pkill -f "uvicorn" || true
pkill -f "vite" || true

# Create logs directory
mkdir -p logs

# Check for Python 3.10+ (required for backend dependencies)
PYTHON_CMD=""
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v python3.10 &> /dev/null; then
    PYTHON_CMD="python3.10"
else
    echo "❌ Python 3.10+ required! Install via:"
    echo "   brew install python@3.10"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip to latest version
echo "🔄 Upgrading pip..."
pip install --upgrade pip

# Install all dependencies
echo "📥 Installing all dependencies..."

# Install root dependencies
echo "📦 Installing root dependencies..."
pip install -r requirements.txt

# Install backend dependencies
echo "📦 Installing backend dependencies..."
pip install -r backend/requirements.txt

# Install RAG system dependencies
echo "📦 Installing RAG system dependencies..."
pip install -r machine_learning/rag_system/requirements.txt

echo "✅ All dependencies installed!"

# Install frontend dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo "📱 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Install marked package if missing
echo "📦 Checking for marked package..."
cd frontend
if ! npm list marked &> /dev/null; then
    echo "📥 Installing marked package..."
    npm install marked
fi
cd ..

# Copy .env files if they don't exist
if [ ! -f "machine_learning/rag_system/.env" ]; then
    echo "⚙️ Creating .env files..."
    cp machine_learning/rag_system/.env.example machine_learning/rag_system/.env 2>/dev/null || true
fi

if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env 2>/dev/null || true
fi

# Warning about .env files
if [ -f "backend/.env" ]; then
    echo "⚠️  WARNING: .env files contain secrets. Make sure they're in .gitignore!"
    echo "⚠️  For production, use environment variables instead of .env files."
fi

echo ""
echo "🚀 Starting all services..."

# Start Frontend
echo "📱 Frontend starting..."
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Start Backend API
echo "⚡ Backend API starting..."
cd backend
../venv/bin/uvicorn src.main:app --reload --port 8000 --host 0.0.0.0 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Start RAG System
echo "🤖 RAG System starting..."
cd machine_learning/rag_system
../../venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8002 > ../../logs/rag_system.log 2>&1 &
RAG_PID=$!
cd ../..

# Cleanup function
cleanup() {
    echo "🛑 Stopping all services..."
    kill $FRONTEND_PID $BACKEND_PID $RAG_PID 2>/dev/null || true
    pkill -f "uvicorn" || true
    pkill -f "vite" || true
}

trap cleanup EXIT

echo ""
echo "✅ All services running!"
echo "🌐 Frontend:    http://localhost:5173"
echo "🔧 Backend:     http://localhost:8000"
echo "🤖 RAG System:  http://localhost:8002"
echo ""
echo "📊 Logs: tail -f logs/frontend.log"
echo "📊 Logs: tail -f logs/backend.log"
echo "📊 Logs: tail -f logs/rag_system.log"
echo ""
echo "Press Ctrl+C to stop all services"

# Keep running
while true; do
    sleep 1
done
