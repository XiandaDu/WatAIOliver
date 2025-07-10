#!/bin/bash

# Standalone run script for WatAIOliver
# Handles setup AND running in one script

echo "Starting WatAIOliver..."

# Kill any existing processes
pkill -f "uvicorn" || true
pkill -f "vite" || true

# Create logs directory
mkdir -p logs

PYTHON_CMD=""

if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
    PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
    if [[ "$PYTHON_VERSION" != "3.12.2" ]]; then
        echo "Python 3.12 is found but not version 3.12.2 (found $PYTHON_VERSION)."
        echo "Please install Python 3.12.2 specifically."
        exit 1
    fi
else
    echo "Python 3.12.2 not found. Attempting to install using Homebrew..."
    if command -v brew &> /dev/null; then
        brew install pyenv
        pyenv install 3.12.2
        pyenv shell 3.12.2
        PYTHON_CMD="$(pyenv which python)"
    else
        echo "ERROR: Homebrew not found. Please install Python 3.12.2 manually from https://www.python.org/downloads/release/python-3122/"
        exit 1
    fi
fi

echo "Using Python command: $PYTHON_CMD"
# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip to latest version
echo "Upgrading pip..."
pip install --upgrade pip

# Install all dependencies
echo "Installing all dependencies..."

# Install root dependencies
echo "Installing root dependencies..."
pip install -r requirements.txt

# Install backend dependencies
echo "Installing backend dependencies..."
pip install -r backend/requirements.txt

# Install RAG system dependencies
echo "Installing RAG system dependencies..."
pip install -r machine_learning/rag_system/requirements.txt

# Install PDF processor dependencies
echo "Installing PDF processor dependencies..."
pip install -r machine_learning/pdf_processor/requirements.txt

echo "All dependencies installed successfully"

# Install frontend dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Install marked package if missing
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

# Start Backend API
echo "Starting backend API..."
cd backend
../venv/bin/uvicorn src.main:app --reload --port 8000 --host 0.0.0.0 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Start PDF Processor
echo "Starting PDF processor..."
cd machine_learning/pdf_processor
../../venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8001 > ../../logs/pdf_processor.log 2>&1 &
PDF_PROCESSOR_PID=$!
cd ../..

# Load and export Google Cloud credentials from RAG system .env file
echo "Loading Google Cloud credentials from .env..."
if [ -f "machine_learning/rag_system/.env" ]; then
    # Source the .env file to get the variables
    set -a  # automatically export all variables
    source machine_learning/rag_system/.env
    set +a  # stop automatically exporting
    
    # Convert relative path to absolute path for GOOGLE_APPLICATION_CREDENTIALS
    if [ ! -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/machine_learning/$(basename $GOOGLE_APPLICATION_CREDENTIALS)"
    fi
    
    # Verify credentials file exists
    if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        echo "ERROR: Google Cloud service account file not found: $GOOGLE_APPLICATION_CREDENTIALS"
        echo "Please ensure the service account JSON file is in the correct location"
        exit 1
    fi
    
    echo "Google Cloud credentials loaded from .env:"
    echo "   Project: $GOOGLE_CLOUD_PROJECT"
    echo "   Service Account: $GOOGLE_APPLICATION_CREDENTIALS"
    echo "   Location: $GOOGLE_CLOUD_LOCATION"
    echo "   Use Vertex AI: $GOOGLE_GENAI_USE_VERTEXAI"
    
    # Verify environment variables are exported
    echo ""
    echo "Verifying environment variables are exported..."
    echo "Google Cloud environment variables:"
    env | grep GOOGLE | while read var; do
        echo "   $var"
    done
    
    # Check if we have the required variables
    if [ -z "$GOOGLE_CLOUD_PROJECT" ] || [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        echo "ERROR: Critical Google Cloud environment variables missing!"
        echo "   GOOGLE_CLOUD_PROJECT: ${GOOGLE_CLOUD_PROJECT:-'NOT SET'}"
        echo "   GOOGLE_APPLICATION_CREDENTIALS: ${GOOGLE_APPLICATION_CREDENTIALS:-'NOT SET'}"
        exit 1
    fi
    
    echo ""
    echo "IMPORTANT: Please ensure these settings are configured:"
    echo ""
    echo "SUPABASE DATABASE SETUP (REQUIRED):"
    echo "   Go to SQL Editor: https://supabase.com/dashboard/project/zeyggksxsfrqziseysnr/sql/new"
    echo "   Run the SQL script in: supabase_setup.sql"
    echo "   Your table: document_embeddings (already exists with test data)"
    echo "   WARNING: Without this, you'll get 'match_documents function not found' errors!"
    echo ""
    echo "GOOGLE CLOUD SETUP (click 'select a project' on top left to choose target project):"
    echo "   Project Dashboard: https://console.cloud.google.com/home/dashboard?project=$GOOGLE_CLOUD_PROJECT"
    echo "   Enable Vertex AI API: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project=$GOOGLE_CLOUD_PROJECT"
    echo "   Check IAM Permissions: https://console.cloud.google.com/iam-admin/iam?project=$GOOGLE_CLOUD_PROJECT"
    echo "   Verify Billing Enabled: https://console.cloud.google.com/billing/projects?project=$GOOGLE_CLOUD_PROJECT"
    echo "   API Dashboard: https://console.cloud.google.com/apis/dashboard?project=$GOOGLE_CLOUD_PROJECT"
    echo ""
    echo "Common error fixes:"
    echo "   - 403 PERMISSION_DENIED -> Check Google Cloud links above"
    echo "   - match_documents not found -> Run supabase_setup.sql in Supabase SQL Editor"
    echo "   - Vertex AI API must be ENABLED"
    echo "   - Service account needs 'Vertex AI User' role"
    echo "   - Billing must be enabled for Vertex AI usage"
else
    echo "ERROR: RAG system .env file not found. Please create machine_learning/rag_system/.env"
    exit 1
fi

# Start RAG System
echo "Starting RAG system..."
cd machine_learning/rag_system
../../venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8002 > ../../logs/rag_system.log 2>&1 &
RAG_PID=$!
cd ../..

# Cleanup function
cleanup() {
    echo "Stopping all services..."
    kill $FRONTEND_PID $BACKEND_PID $PDF_PROCESSOR_PID $RAG_PID 2>/dev/null || true
    pkill -f "uvicorn" || true
    pkill -f "vite" || true
}

trap cleanup EXIT

echo ""
echo "All services running successfully!"
echo "Frontend:       http://localhost:5173"
echo "Backend:        http://localhost:8000"
echo "PDF Processor:  http://localhost:8001"
echo "RAG System:     http://localhost:8002"
echo ""
echo "Logs: tail -f logs/frontend.log"
echo "Logs: tail -f logs/backend.log"
echo "Logs: tail -f logs/pdf_processor.log"
echo "Logs: tail -f logs/rag_system.log"
echo ""
echo "Press Ctrl+C to stop all services"

# Keep running
while true; do
    sleep 1
done
