#!/bin/bash
# KOR'TANA Run and Monitor Script
# Sets up environment, starts the backend, and monitors autonomous development

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${SCRIPT_DIR}/backend"
BACKEND_PORT="${BACKEND_PORT:-8000}"
MONITORING_MODE="${MONITORING_MODE:-dashboard}"  # dashboard, status, or cycle

# Print colored message
print_msg() {
    local color=$1
    shift
    echo -e "${color}$@${NC}"
}

print_header() {
    echo ""
    print_msg "$MAGENTA" "=============================================================================="
    print_msg "$MAGENTA" "$@"
    print_msg "$MAGENTA" "=============================================================================="
    echo ""
}

print_step() {
    print_msg "$CYAN" "➜ $@"
}

print_success() {
    print_msg "$GREEN" "✅ $@"
}

print_error() {
    print_msg "$RED" "❌ $@"
}

print_warning() {
    print_msg "$YELLOW" "⚠️  $@"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_header "🔍 CHECKING PREREQUISITES"
    
    local all_ok=true
    
    # Check Python
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        print_success "Python: $PYTHON_VERSION"
    else
        print_error "Python 3 not found"
        all_ok=false
    fi
    
    # Check pip
    if command_exists pip3; then
        print_success "pip3: Available"
    else
        print_error "pip3 not found"
        all_ok=false
    fi
    
    # Check Docker
    if command_exists docker; then
        DOCKER_VERSION=$(docker --version 2>&1 | awk '{print $3}' | tr -d ',')
        print_success "Docker: $DOCKER_VERSION"
    else
        print_warning "Docker not found (optional but recommended)"
    fi
    
    # Check httpx for monitoring script
    if python3 -c "import httpx" 2>/dev/null; then
        print_success "httpx: Available"
    else
        print_warning "httpx not installed (required for monitoring)"
        print_step "Installing httpx..."
        pip3 install httpx --quiet
        print_success "httpx installed"
    fi
    
    if [ "$all_ok" = false ]; then
        print_error "Missing required prerequisites"
        exit 1
    fi
    
    echo ""
}

# Setup environment
setup_environment() {
    print_header "⚙️  SETTING UP ENVIRONMENT"
    
    # Check if .env exists
    if [ ! -f "${BACKEND_DIR}/.env" ]; then
        print_step "Creating .env file from template..."
        cp "${BACKEND_DIR}/.env.example" "${BACKEND_DIR}/.env"
        print_success "Created ${BACKEND_DIR}/.env"
        print_warning "Please update .env with your actual API keys!"
        echo ""
    else
        print_success ".env file exists"
    fi
    
    # Check if environment variables are set
    if [ -f "${BACKEND_DIR}/.env" ]; then
        source "${BACKEND_DIR}/.env" 2>/dev/null || true
        
        if [ -z "$GITHUB_TOKEN" ] || [ "$GITHUB_TOKEN" = "your_github_token_here" ]; then
            print_warning "GITHUB_TOKEN not configured in .env"
        fi
        
        if [ -z "$GEMINI_API_KEY" ] || [ "$GEMINI_API_KEY" = "your_gemini_api_key_here" ]; then
            print_warning "GEMINI_API_KEY not configured in .env"
        fi
        
        if [ -z "$DATABASE_URL" ]; then
            print_warning "DATABASE_URL not configured in .env"
        fi
    fi
    
    echo ""
}

# Install dependencies
install_dependencies() {
    print_header "📦 INSTALLING DEPENDENCIES"
    
    print_step "Installing backend Python dependencies..."
    cd "${BACKEND_DIR}"
    
    # Check if virtual environment should be used
    if [ ! -d "venv" ]; then
        print_step "Creating Python virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    pip3 install -r requirements.txt --quiet
    print_success "Backend dependencies installed"
    
    cd "${SCRIPT_DIR}"
    echo ""
}

# Start backend with Docker
start_backend_docker() {
    print_header "🚀 STARTING BACKEND WITH DOCKER"
    
    print_step "Starting Docker Compose services..."
    docker compose up -d
    
    print_success "Docker services started"
    print_step "Waiting for services to be ready..."
    sleep 5
    
    # Check if backend is running
    for i in {1..30}; do
        if curl -s "http://localhost:${BACKEND_PORT}/api/health" >/dev/null 2>&1; then
            print_success "Backend is ready!"
            break
        fi
        
        if [ $i -eq 30 ]; then
            print_error "Backend failed to start after 30 seconds"
            docker compose logs backend
            exit 1
        fi
        
        sleep 1
    done
    
    echo ""
}

# Start backend locally (without Docker)
start_backend_local() {
    print_header "🚀 STARTING BACKEND LOCALLY"
    
    cd "${BACKEND_DIR}"
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_error "Virtual environment not found. Run with --install first."
        exit 1
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    print_step "Starting FastAPI backend on port ${BACKEND_PORT}..."
    
    # Start backend in background
    nohup python3 -m uvicorn main:app --host 0.0.0.0 --port ${BACKEND_PORT} --reload > backend.log 2>&1 &
    BACKEND_PID=$!
    
    print_success "Backend started (PID: ${BACKEND_PID})"
    print_step "Log file: ${BACKEND_DIR}/backend.log"
    
    # Wait for backend to be ready
    print_step "Waiting for backend to be ready..."
    for i in {1..30}; do
        if curl -s "http://localhost:${BACKEND_PORT}/api/health" >/dev/null 2>&1; then
            print_success "Backend is ready!"
            break
        fi
        
        if [ $i -eq 30 ]; then
            print_error "Backend failed to start after 30 seconds"
            cat "${BACKEND_DIR}/backend.log"
            exit 1
        fi
        
        sleep 1
    done
    
    cd "${SCRIPT_DIR}"
    echo ""
}

# Show backend info
show_backend_info() {
    print_header "📊 BACKEND INFORMATION"
    
    # Get health status
    HEALTH_JSON=$(curl -s "http://localhost:${BACKEND_PORT}/api/health" || echo "{}")
    
    echo "🔗 Backend URL: http://localhost:${BACKEND_PORT}"
    echo "📚 API Docs: http://localhost:${BACKEND_PORT}/docs"
    echo "🏥 Health Check: http://localhost:${BACKEND_PORT}/api/health"
    echo ""
    echo "Health Status:"
    echo "$HEALTH_JSON" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_JSON"
    echo ""
}

# Start monitoring
start_monitoring() {
    print_header "👁️  STARTING AUTONOMOUS DEVELOPMENT MONITOR"
    
    export KORTANA_BACKEND_URL="http://localhost:${BACKEND_PORT}"
    
    case "$MONITORING_MODE" in
        dashboard)
            print_step "Starting real-time dashboard (Ctrl+C to stop)..."
            sleep 2
            python3 "${SCRIPT_DIR}/monitor_autonomous_dev.py"
            ;;
        status)
            print_step "Fetching quick status..."
            python3 "${SCRIPT_DIR}/monitor_autonomous_dev.py" status
            ;;
        cycle)
            print_step "Triggering autonomous cycle..."
            python3 "${SCRIPT_DIR}/monitor_autonomous_dev.py" cycle
            ;;
        *)
            print_error "Unknown monitoring mode: $MONITORING_MODE"
            exit 1
            ;;
    esac
}

# Cleanup function
cleanup() {
    print_header "🧹 CLEANUP"
    
    if [ "$USE_DOCKER" = true ]; then
        print_step "Stopping Docker services..."
        docker compose down
        print_success "Docker services stopped"
    else
        if [ -n "$BACKEND_PID" ]; then
            print_step "Stopping backend (PID: ${BACKEND_PID})..."
            kill $BACKEND_PID 2>/dev/null || true
            print_success "Backend stopped"
        fi
    fi
}

# Print usage
usage() {
    cat << EOF
KOR'TANA Run and Monitor Script

Usage:
    $0 [OPTIONS]

Options:
    --docker            Use Docker Compose (default)
    --local             Run backend locally without Docker
    --install           Install dependencies before running
    --status            Show quick status instead of monitoring
    --cycle             Trigger one autonomous cycle
    --help              Show this help message

Environment Variables:
    BACKEND_PORT        Backend port (default: 8000)
    MONITORING_MODE     Monitoring mode: dashboard, status, or cycle (default: dashboard)

Examples:
    $0                  Start with Docker and monitor
    $0 --local          Start locally without Docker
    $0 --status         Quick status check
    $0 --cycle          Trigger one autonomous cycle
    
EOF
}

# Main execution
main() {
    print_header "🤖 KOR'TANA - AUTONOMOUS DEVELOPMENT SYSTEM"
    
    # Parse arguments
    USE_DOCKER=true
    INSTALL_DEPS=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --docker)
                USE_DOCKER=true
                shift
                ;;
            --local)
                USE_DOCKER=false
                shift
                ;;
            --install)
                INSTALL_DEPS=true
                shift
                ;;
            --status)
                MONITORING_MODE="status"
                shift
                ;;
            --cycle)
                MONITORING_MODE="cycle"
                shift
                ;;
            --help)
                usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
    
    # Check prerequisites
    check_prerequisites
    
    # Setup environment
    setup_environment
    
    # Install dependencies if requested
    if [ "$INSTALL_DEPS" = true ] || [ "$USE_DOCKER" = false ]; then
        install_dependencies
    fi
    
    # Start backend
    if [ "$USE_DOCKER" = true ]; then
        start_backend_docker
    else
        start_backend_local
    fi
    
    # Show backend info
    show_backend_info
    
    # Start monitoring
    start_monitoring
    
    # Cleanup on exit (only for local mode)
    if [ "$USE_DOCKER" = false ]; then
        trap cleanup EXIT
    fi
}

# Run main function
main "$@"
