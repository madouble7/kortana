#!/bin/bash
# Start Kor'tana with CopilotKit Frontend
# This script starts both the backend and frontend servers

echo "🚀 Starting Kor'tana with CopilotKit Integration"
echo "=================================================="
echo ""

# Check if required dependencies are installed
echo "Checking dependencies..."

# Check Python (try python3 first, then python)
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "❌ Python is not installed (tried python3 and python)"
    exit 1
fi

echo "Using Python: $PYTHON_CMD"

# Check Node
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    exit 1
fi

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found"
    echo "   Creating .env from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "   Please edit .env and add your API keys"
    else
        cat > .env << 'ENVEOF'
# Kor'tana Configuration
KORTANA_API_KEY=your_api_key_here
LOG_LEVEL=INFO

# LLM Configuration
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Database
MEMORY_DB_URL=sqlite:///./kortana_memory_dev.db
ENVEOF
        echo "   .env file created. Please edit it and add your API keys"
    fi
    echo ""
fi

# Install frontend dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend && npm install && cd ..
    echo ""
fi

echo "✅ All checks passed!"
echo ""
echo "Starting servers..."
echo "- Backend will be available at: http://localhost:8000"
echo "- Frontend will be available at: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup INT TERM

# Start backend
echo "🔧 Starting backend server..."
$PYTHON_CMD -m uvicorn src.kortana.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 3

# Start frontend
echo "🎨 Starting frontend server..."
cd frontend && npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✨ Kor'tana is running!"
echo ""
echo "📱 Open your browser to http://localhost:5173 to access the CopilotKit interface"
echo "📚 Backend API documentation: http://localhost:8000/docs"
echo ""

# Wait for both processes
wait
