#!/bin/bash

# RAG System Setup Script
# This script sets up a virtual environment and installs all dependencies

echo "🚀 Setting up RAG System..."

# Check if Python 3.8+ is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your actual credentials before running the application."
else
    echo "✅ .env file found."
fi

echo "✅ Setup complete!"
echo ""
echo "🌟 Starting FastAPI server..."
echo "📍 Server will be available at: http://localhost:8000"
echo "📖 API Documentation: http://localhost:8000/docs"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

# Start the server within the activated virtual environment
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 