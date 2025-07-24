#!/bin/bash

FRONTEND_PORT=5173
BACKEND_PORT=8000
PDF_PROCESSOR_PORT=8001
RAG_SYSTEM_PORT=8002
SPECULATIVE_AI_PORT=8003
DEFAULT_HOST="0.0.0.0"

echo "Starting WatAIOliver..."

# Kill old processes
if [[ "$OS" == "Windows_NT" ]]; then
    echo "Killing processes on Windows..."
    taskkill //IM uvicorn.exe //F 2>nul || true
    taskkill //IM vite.exe //F 2>nul || true
else
    echo "Killing processes on Unix..."
    pkill -f "uvicorn" || true
    pkill -f "vite" || true
fi

# Kill processes using our specific ports
lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null || true
lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null || true
lsof -ti:$PDF_PROCESSOR_PORT | xargs kill -9 2>/dev/null || true
lsof -ti:$RAG_SYSTEM_PORT | xargs kill -9 2>/dev/null || true
lsof -ti:$SPECULATIVE_AI_PORT | xargs kill -9 2>/dev/null || true

# Wait a moment for ports to be freed
sleep 2

# Create logs directory
mkdir -p logs

PYTHON_CMD=""
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
    PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
    if [[ "$PYTHON_VERSION" != "3.12.2" ]]; then
        echo "ERROR: Python 3.12.2 is required. Found version $PYTHON_VERSION."
        echo "Please install Python 3.12.2 or use the manual setup approach in windows_proj_env_setup.md"
        exit 1
    fi
else
    echo "ERROR: Python 3.12.2 not found."
    echo "Please install Python 3.12.2 or use the manual setup approach in windows_proj_env_setup.md"
    exit 1
fi

echo "Using Python command: $PYTHON_CMD"

# Virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    if [ ! -d "venv" ]; then
        echo "ERROR: Virtual environment creation failed!"
        exit 1
    fi
fi

# Correct venv paths
if [[ "$OS" == "Windows_NT" ]]; then
    ACTIVATE_PATH="venv/Scripts/activate"
    UVICORN_PATH="venv/Scripts/uvicorn.exe"
else
    ACTIVATE_PATH="venv/bin/activate"
    UVICORN_PATH="venv/bin/uvicorn"
fi

echo "Activating virtual environment: $ACTIVATE_PATH"
source "$ACTIVATE_PATH"

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install all dependencies
echo "Installing all dependencies..."

echo "Installing backend dependencies..."
pip install -r backend/requirements.txt || true

echo "Installing RAG system dependencies..."
pip install -r machine_learning/rag_system/requirements.txt || true

echo "Installing PDF processor dependencies..."
pip install -r machine_learning/pdf_processor/requirements.txt || true

# Install Agents system dependencies
echo "Installing Agents system dependencies..."
pip install -r machine_learning/ai_agents/requirements.txt

echo "All dependencies installed successfully"

# Install frontend dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Ensure marked package
echo "Checking for marked package..."
cd frontend
if ! npm list marked &> /dev/null; then
    echo "Installing marked package..."
    npm install marked
fi
cd ..

echo ""
echo "Starting all services..."

# Start Frontend
echo "Starting frontend server..."
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Start Backend
echo "Starting backend API..."
cd backend
source ../venv/bin/activate
uvicorn src.main:app --reload --port $BACKEND_PORT --host $DEFAULT_HOST > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Start PDF Processor
echo "Starting PDF processor..."
cd machine_learning/pdf_processor
source ../../venv/bin/activate
uvicorn main:app --reload --host $DEFAULT_HOST --port $PDF_PROCESSOR_PORT > ../../logs/pdf_processor.log 2>&1 &
PDF_PROCESSOR_PID=$!
cd ../..

# Load GCP env
echo "Loading Google Cloud credentials from .env..."
if [ -f "machine_learning/rag_system/.env" ]; then
    set -a
    source machine_learning/rag_system/.env
    set +a

    if [ ! -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/machine_learning/$(basename "$GOOGLE_APPLICATION_CREDENTIALS")"
    fi

    if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        echo "ERROR: Service account file missing: $GOOGLE_APPLICATION_CREDENTIALS"
        exit 1
    fi

    echo "Google Cloud credentials loaded from .env:"
    echo "   Project: $GOOGLE_CLOUD_PROJECT"
    echo "   Service Account: $GOOGLE_APPLICATION_CREDENTIALS"
    echo "   Location: $GOOGLE_CLOUD_LOCATION"
    echo "   Use Vertex AI: $GOOGLE_GENAI_USE_VERTEXAI"
else
    echo "ERROR: RAG system .env file not found."
    exit 1
fi

# Start RAG System
echo "Starting RAG system..."
cd machine_learning
source ../venv/bin/activate
uvicorn rag_system.app.main:app --reload --host $DEFAULT_HOST --port $RAG_SYSTEM_PORT > ../logs/rag_system.log 2>&1 &
RAG_PID=$!
cd ..

# Start Agents System
echo "Starting Agents system..."
cd machine_learning
source ../venv/bin/activate
uvicorn ai_agents.app.main:app --reload --host $DEFAULT_HOST --port $SPECULATIVE_AI_PORT > ../logs/agents.log 2>&1 &
SPECULATIVE_AI_PID=$!
cd ..

# Cleanup trap
cleanup() {
    echo "Stopping all services..."
    kill $FRONTEND_PID $BACKEND_PID $PDF_PROCESSOR_PID $RAG_PID $SPECULATIVE_AI_PID 2>/dev/null || true
    
    if [[ "$OS" == "Windows_NT" ]]; then
        taskkill //IM uvicorn.exe //F 2>nul || true
        taskkill //IM vite.exe //F 2>nul || true
    else
        pkill -f "uvicorn" || true
        pkill -f "vite" || true
    fi
}
trap cleanup EXIT

echo ""
echo "All services running successfully!"
echo "Frontend:         http://localhost:$FRONTEND_PORT"
echo "Backend:          http://localhost:$BACKEND_PORT"
echo "PDF Processor:    http://localhost:$PDF_PROCESSOR_PORT"
echo "RAG System:       http://localhost:$RAG_SYSTEM_PORT"
echo "Agents System:    http://localhost:$SPECULATIVE_AI_PORT"
echo ""
echo "Logs: tail -f logs/frontend.log"
echo "Logs: tail -f logs/backend.log"
echo "Logs: tail -f logs/pdf_processor.log"
echo "Logs: tail -f logs/rag_system.log"
echo "Logs: tail -f logs/agents.log"
echo ""
echo "Press Ctrl+C to stop all services"

while true; do
    sleep 1
done
