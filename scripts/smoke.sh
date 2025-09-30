#!/bin/bash
# Smoke tests for Print Advisor Docker stack

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
WEB_URL="http://localhost:8000"
TIMEOUT=60
RETRY_INTERVAL=5

echo -e "${YELLOW}🚀 Starting Print Advisor smoke tests...${NC}"

# Function to check if service is ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local timeout=$3
    local retry_interval=$4
    
    echo -e "${YELLOW}⏳ Waiting for $service_name to be ready...${NC}"
    
    local elapsed=0
    while [ $elapsed -lt $timeout ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is ready!${NC}"
            return 0
        fi
        
        sleep $retry_interval
        elapsed=$((elapsed + retry_interval))
        echo -e "${YELLOW}   Still waiting... (${elapsed}s/${timeout}s)${NC}"
    done
    
    echo -e "${RED}❌ $service_name failed to become ready within ${timeout}s${NC}"
    return 1
}

# Function to test URL
test_url() {
    local url=$1
    local expected_status=${2:-200}
    local description=$3
    
    echo -e "${YELLOW}🔍 Testing: $description${NC}"
    
    local status_code
    status_code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$status_code" -eq "$expected_status" ]; then
        echo -e "${GREEN}✅ $description - Status: $status_code${NC}"
        return 0
    else
        echo -e "${RED}❌ $description - Expected: $expected_status, Got: $status_code${NC}"
        return 1
    fi
}

# Function to run Django management command
run_django_command() {
    local command=$1
    local description=$2
    
    echo -e "${YELLOW}🔍 Running: $description${NC}"
    
    if docker compose exec -T web python manage.py $command; then
        echo -e "${GREEN}✅ $description - Success${NC}"
        return 0
    else
        echo -e "${RED}❌ $description - Failed${NC}"
        return 1
    fi
}

# Main smoke test execution
main() {
    local failed_tests=0
    
    # Wait for web service to be ready
    if ! wait_for_service "$WEB_URL/health/" "Web service" $TIMEOUT $RETRY_INTERVAL; then
        echo -e "${RED}❌ Web service health check failed${NC}"
        exit 1
    fi
    
    # Test health endpoint
    if ! test_url "$WEB_URL/health/" 200 "Health endpoint"; then
        ((failed_tests++))
    fi
    
    # Test main dashboard (should redirect to login)
    if ! test_url "$WEB_URL/" 302 "Main dashboard (redirect to login)"; then
        ((failed_tests++))
    fi
    
    # Test admin login page
    if ! test_url "$WEB_URL/admin/login/" 200 "Admin login page"; then
        ((failed_tests++))
    fi
    
    # Test Django deployment check
    if ! run_django_command "check --deploy" "Django deployment check"; then
        ((failed_tests++))
    fi
    
    # Test database migrations
    if ! run_django_command "migrate --check" "Database migrations check"; then
        ((failed_tests++))
    fi
    
    # Test static files collection
    if ! run_django_command "collectstatic --noinput --dry-run" "Static files check"; then
        ((failed_tests++))
    fi
    
    # Check if watcher is running
    echo -e "${YELLOW}🔍 Checking watcher service...${NC}"
    if docker compose exec -T watcher pgrep -f "printing.print_events_watcher" > /dev/null; then
        echo -e "${GREEN}✅ Watcher service is running${NC}"
    else
        echo -e "${RED}❌ Watcher service is not running${NC}"
        ((failed_tests++))
    fi
    
    # Check database connectivity
    echo -e "${YELLOW}🔍 Checking database connectivity...${NC}"
    if docker compose exec -T db pg_isready -U advisor -d advisor; then
        echo -e "${GREEN}✅ Database is ready${NC}"
    else
        echo -e "${RED}❌ Database is not ready${NC}"
        ((failed_tests++))
    fi
    
    # Summary
    echo -e "\n${YELLOW}📊 Smoke test summary:${NC}"
    if [ $failed_tests -eq 0 ]; then
        echo -e "${GREEN}🎉 All smoke tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}❌ $failed_tests test(s) failed${NC}"
        exit 1
    fi
}

# Run main function
main "$@"

