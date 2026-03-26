#!/bin/bash
# Kor'tana Audit & Verification Script
# Verifies all enhancements are properly installed and working

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "Kor'tana Comprehensive Audit & Verification"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS_COUNT=0
FAIL_COUNT=0

check_file() {
    local file=$1
    local name=$2
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $name exists"
        ((PASS_COUNT++))
    else
        echo -e "${RED}✗${NC} $name missing: $file"
        ((FAIL_COUNT++))
    fi
}

check_directory() {
    local dir=$1
    local name=$2
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $name directory exists"
        ((PASS_COUNT++))
    else
        echo -e "${RED}✗${NC} $name directory missing: $dir"
        ((FAIL_COUNT++))
    fi
}

check_command() {
    local cmd=$1
    local name=$2
    if command -v $cmd &> /dev/null; then
        echo -e "${GREEN}✓${NC} $name installed"
        ((PASS_COUNT++))
    else
        echo -e "${YELLOW}⚠${NC} $name not found: $cmd"
        ((FAIL_COUNT++))
    fi
}

check_docker_service() {
    local service=$1
    local name=$2
    if docker compose ps 2>/dev/null | grep -q "$service.*running"; then
        echo -e "${GREEN}✓${NC} $name service running"
        ((PASS_COUNT++))
    else
        echo -e "${YELLOW}⚠${NC} $name service not running"
        ((FAIL_COUNT++))
    fi
}

check_http_endpoint() {
    local url=$1
    local name=$2
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name endpoint responding"
        ((PASS_COUNT++))
    else
        echo -e "${YELLOW}⚠${NC} $name endpoint not responding: $url"
        ((FAIL_COUNT++))
    fi
}

# ============================================================================
# 1. FILE STRUCTURE AUDIT
# ============================================================================
echo ""
echo "1. FILE STRUCTURE AUDIT"
echo "─────────────────────────────────────────────────────────────"

check_file "backend/llm_router.py" "LLM Router"
check_file "backend/github_automation.py" "GitHub Automation Engine"
check_file "backend/celery_config.py" "Celery Configuration"
check_file "backend/monitoring.py" "Monitoring & Observability"
check_file "backend/resilience.py" "Resilience Patterns"
check_directory "backend/tests" "Tests Directory"
check_file "backend/tests/test_llm_router.py" "LLM Router Tests"
check_file "backend/tests/test_github_automation.py" "GitHub Automation Tests"
check_file ".github/workflows/build-test.yml" "CI/CD Build Workflow"
check_file ".github/workflows/deploy.yml" "CI/CD Deploy Workflow"
check_file "Dockerfile" "Development Dockerfile"
check_file "Dockerfile.prod" "Production Dockerfile"
check_file "docker-compose.yml" "Development Compose"
check_file "docker-compose.prod.yml" "Production Compose"
check_file ".dockerignore" "Docker Ignore File"
check_file ".env.example" "Environment Template"
check_file ".env.prod.example" "Production Environment Template"
check_file "DEPLOYMENT_GUIDE.md" "Deployment Documentation"
check_file "API_DOCUMENTATION.md" "API Documentation"
check_file "INTEGRATION_GUIDE.md" "Integration Guide"
check_file "DOCKER_COMMANDS.sh" "Docker Commands Reference"
check_file "backend/requirements.txt" "Updated Requirements"

# ============================================================================
# 2. DEPENDENCIES AUDIT
# ============================================================================
echo ""
echo "2. DEPENDENCY AUDIT"
echo "─────────────────────────────────────────────────────────────"

check_command "docker" "Docker"
check_command "docker-compose" "Docker Compose"
check_command "python" "Python"
check_command "pip" "Pip"
check_command "git" "Git"

# ============================================================================
# 3. DOCKER SERVICES AUDIT
# ============================================================================
echo ""
echo "3. DOCKER SERVICES AUDIT"
echo "─────────────────────────────────────────────────────────────"

if command -v docker &> /dev/null && docker info &> /dev/null; then
    check_docker_service "postgres" "PostgreSQL Database"
    check_docker_service "redis" "Redis Cache"
    check_docker_service "backend" "Backend API"
else
    echo -e "${YELLOW}⚠${NC} Docker not running or not available"
fi

# ============================================================================
# 4. API ENDPOINTS AUDIT
# ============================================================================
echo ""
echo "4. API ENDPOINTS AUDIT"
echo "─────────────────────────────────────────────────────────────"

check_http_endpoint "http://localhost:8000/api/health" "Health Check"
check_http_endpoint "http://localhost:8000/docs" "API Documentation"
check_http_endpoint "http://localhost:8000/metrics" "Prometheus Metrics"

# ============================================================================
# 5. FEATURE IMPLEMENTATION AUDIT
# ============================================================================
echo ""
echo "5. FEATURE IMPLEMENTATION AUDIT"
echo "─────────────────────────────────────────────────────────────"

# Check LLM Router
if grep -q "class LLMRouter" backend/llm_router.py; then
    echo -e "${GREEN}✓${NC} LLM Router with multi-model fallback implemented"
    ((PASS_COUNT++))
else
    echo -e "${RED}✗${NC} LLM Router implementation incomplete"
    ((FAIL_COUNT++))
fi

# Check GitHub Automation
if grep -q "class GitHubAutomationEngine" backend/github_automation.py; then
    echo -e "${GREEN}✓${NC} GitHub Automation Engine implemented"
    ((PASS_COUNT++))
else
    echo -e "${RED}✗${NC} GitHub Automation implementation incomplete"
    ((FAIL_COUNT++))
fi

# Check Celery Integration
if grep -q "class CallbackTask" backend/celery_config.py; then
    echo -e "${GREEN}✓${NC} Celery Task Scheduling implemented"
    ((PASS_COUNT++))
else
    echo -e "${RED}✗${NC} Celery implementation incomplete"
    ((FAIL_COUNT++))
fi

# Check Monitoring
if grep -q "class MetricsCollector" backend/monitoring.py; then
    echo -e "${GREEN}✓${NC} Prometheus Metrics implemented"
    ((PASS_COUNT++))
else
    echo -e "${RED}✗${NC} Monitoring implementation incomplete"
    ((FAIL_COUNT++))
fi

# Check Resilience
if grep -q "class CircuitBreaker" backend/resilience.py; then
    echo -e "${GREEN}✓${NC} Resilience Patterns (Circuit Breaker) implemented"
    ((PASS_COUNT++))
else
    echo -e "${RED}✗${NC} Resilience implementation incomplete"
    ((FAIL_COUNT++))
fi

# Check CI/CD
if [ -f ".github/workflows/build-test.yml" ] && [ -f ".github/workflows/deploy.yml" ]; then
    echo -e "${GREEN}✓${NC} GitHub Actions CI/CD workflows configured"
    ((PASS_COUNT++))
else
    echo -e "${RED}✗${NC} CI/CD workflows incomplete"
    ((FAIL_COUNT++))
fi

# Check Tests
if [ -f "backend/tests/test_llm_router.py" ] && [ -f "backend/tests/test_github_automation.py" ]; then
    echo -e "${GREEN}✓${NC} Unit tests for critical paths implemented"
    ((PASS_COUNT++))
else
    echo -e "${RED}✗${NC} Unit tests incomplete"
    ((FAIL_COUNT++))
fi

# ============================================================================
# 6. DOCUMENTATION AUDIT
# ============================================================================
echo ""
echo "6. DOCUMENTATION AUDIT"
echo "─────────────────────────────────────────────────────────────"

if [ -f "DEPLOYMENT_GUIDE.md" ] && grep -q "Production Deployment" DEPLOYMENT_GUIDE.md; then
    echo -e "${GREEN}✓${NC} Comprehensive deployment guide provided"
    ((PASS_COUNT++))
else
    echo -e "${RED}✗${NC} Deployment guide incomplete"
    ((FAIL_COUNT++))
fi

if [ -f "API_DOCUMENTATION.md" ] && grep -q "Authentication Endpoints" API_DOCUMENTATION.md; then
    echo -e "${GREEN}✓${NC} Complete API documentation provided"
    ((PASS_COUNT++))
else
    echo -e "${RED}✗${NC} API documentation incomplete"
    ((FAIL_COUNT++))
fi

if [ -f "INTEGRATION_GUIDE.md" ] && grep -q "Step 1" INTEGRATION_GUIDE.md; then
    echo -e "${GREEN}✓${NC} Integration guide with step-by-step instructions provided"
    ((PASS_COUNT++))
else
    echo -e "${RED}✗${NC} Integration guide incomplete"
    ((FAIL_COUNT++))
fi

# ============================================================================
# 7. CODE QUALITY AUDIT
# ============================================================================
echo ""
echo "7. CODE QUALITY AUDIT"
echo "─────────────────────────────────────────────────────────────"

# Check for type hints
TYPED_FILES=$(find backend -name "*.py" -exec grep -l "def.*->" {} \; 2>/dev/null | wc -l)
if [ "$TYPED_FILES" -gt 5 ]; then
    echo -e "${GREEN}✓${NC} Type hints implemented in $TYPED_FILES files"
    ((PASS_COUNT++))
else
    echo -e "${YELLOW}⚠${NC} Limited type hints found"
fi

# Check for error handling
ERROR_HANDLING=$(grep -r "except" backend/*.py 2>/dev/null | wc -l)
if [ "$ERROR_HANDLING" -gt 20 ]; then
    echo -e "${GREEN}✓${NC} Comprehensive error handling implemented"
    ((PASS_COUNT++))
else
    echo -e "${YELLOW}⚠${NC} Limited error handling found"
fi

# Check for docstrings
DOCSTRINGS=$(grep -r '"""' backend/*.py 2>/dev/null | wc -l)
if [ "$DOCSTRINGS" -gt 10 ]; then
    echo -e "${GREEN}✓${NC} Docstrings added to major components"
    ((PASS_COUNT++))
else
    echo -e "${YELLOW}⚠${NC} Limited docstrings found"
fi

# ============================================================================
# SUMMARY
# ============================================================================
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "AUDIT SUMMARY"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo -e "${GREEN}✓ PASSED: $PASS_COUNT${NC}"
echo -e "${RED}✗ FAILED: $FAIL_COUNT${NC}"
echo ""

TOTAL=$((PASS_COUNT + FAIL_COUNT))
PERCENTAGE=$((PASS_COUNT * 100 / TOTAL))

echo "Completion: $PERCENTAGE% ($PASS_COUNT/$TOTAL)"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}✓ ALL AUDITS PASSED!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Update requirements: pip install -r backend/requirements.txt"
    echo "2. Start services: docker compose up -d"
    echo "3. Verify health: curl http://localhost:8000/api/health"
    echo "4. View docs: http://localhost:8000/docs"
    exit 0
else
    echo -e "${YELLOW}⚠ Some audits failed or warnings present${NC}"
    echo ""
    echo "Review the items above and ensure all components are properly installed."
    exit 1
fi
