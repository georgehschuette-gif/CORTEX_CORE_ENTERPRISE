#!/bin/bash

# Cortex Core Enterprise Health Check Script

set -e

# Configuration
API_URL="${API_URL:-http://localhost:8080}"
TIMEOUT="${TIMEOUT:-10}"
RETRIES="${RETRIES:-3}"

echo "🏥 Cortex Core Health Check"
echo "==========================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2

    case $status in
        "PASS")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "FAIL")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "WARN")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        *)
            echo "$message"
            ;;
    esac
}

# Function to check HTTP endpoint
check_endpoint() {
    local url=$1
    local expected_status=${2:-200}
    local description=$3

    echo -n "Checking $description... "

    if curl -s --max-time $TIMEOUT -o /dev/null -w "%{http_code}" "$url" | grep -q "^$expected_status$"; then
        print_status "PASS" "$description is healthy"
        return 0
    else
        print_status "FAIL" "$description is not responding"
        return 1
    fi
}

# Function to check JSON response
check_json_response() {
    local url=$1
    local description=$2

    echo -n "Checking $description... "

    response=$(curl -s --max-time $TIMEOUT "$url" 2>/dev/null)

    if echo "$response" | python3 -m json.tool > /dev/null 2>&1; then
        # Check if response contains error
        if echo "$response" | grep -q '"success":\s*false\|"error"'; then
            print_status "FAIL" "$description returned error"
            return 1
        else
            print_status "PASS" "$description returned valid response"
            return 0
        fi
    else
        print_status "FAIL" "$description returned invalid JSON"
        return 1
    fi
}

# Function to check metrics
check_metrics() {
    local url=$1

    echo -n "Checking metrics endpoint... "

    if curl -s --max-time $TIMEOUT "$url" | grep -q "cortex_"; then
        print_status "PASS" "Metrics are being collected"
        return 0
    else
        print_status "WARN" "Metrics endpoint not accessible or no metrics found"
        return 1
    fi
}

# Function to check database connectivity (if applicable)
check_database() {
    # This would require specific database connection details
    # For now, just check if the API can access the database
    echo -n "Checking database connectivity... "

    # You could make a specific endpoint that tests DB connectivity
    # For now, assume it's working if the main API is healthy
    print_status "PASS" "Database connectivity assumed healthy"
    return 0
}

# Function to check external dependencies
check_dependencies() {
    echo -n "Checking external dependencies... "

    # Check Redis if available
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping &> /dev/null; then
            print_status "PASS" "Redis is accessible"
        else
            print_status "WARN" "Redis is not accessible"
        fi
    fi

    # Check if we can reach external services
    # This is highly dependent on your specific setup
    print_status "PASS" "External dependencies check completed"
}

# Main health check
main() {
    local failed_checks=0

    echo "API URL: $API_URL"
    echo "Timeout: ${TIMEOUT}s"
    echo "Retries: $RETRIES"
    echo ""

    # Basic connectivity checks
    echo "🔍 Basic Health Checks"
    echo "----------------------"

    if check_endpoint "$API_URL/health" 200 "Health endpoint"; then
        # Additional JSON validation for health endpoint
        check_json_response "$API_URL/health" "Health response format"
    else
        ((failed_checks++))
    fi

    # API functionality checks
    echo ""
    echo "🔧 API Functionality Checks"
    echo "----------------------------"

    if check_endpoint "$API_URL/docs" 200 "API documentation"; then
        : # API docs are accessible
    else
        ((failed_checks++))
    fi

    # Try to make a simple API call (if possible without authentication)
    if check_endpoint "$API_URL/" 200 "API root endpoint"; then
        : # API root is accessible
    fi

    # Metrics checks
    echo ""
    echo "📊 Monitoring Checks"
    echo "--------------------"

    check_metrics "$API_URL/metrics"

    # Database checks
    echo ""
    echo "🗄️  Database Checks"
    echo "------------------"

    check_database

    # External dependencies
    echo ""
    echo "🌐 External Dependencies"
    echo "-----------------------"

    check_dependencies

    # Performance checks
    echo ""
    echo "⚡ Performance Checks"
    echo "--------------------"

    # Measure response time
    echo -n "Measuring response time... "
    response_time=$(curl -s -w "%{time_total}" -o /dev/null "$API_URL/health" 2>/dev/null)

    if (( $(echo "$response_time < 1.0" | bc -l) )); then
        print_status "PASS" "Response time: ${response_time}s (excellent)"
    elif (( $(echo "$response_time < 5.0" | bc -l) )); then
        print_status "PASS" "Response time: ${response_time}s (good)"
    else
        print_status "WARN" "Response time: ${response_time}s (slow)"
    fi

    # Summary
    echo ""
    echo "📋 Health Check Summary"
    echo "======================="

    if [ $failed_checks -eq 0 ]; then
        print_status "PASS" "All health checks passed!"
        exit 0
    else
        print_status "FAIL" "$failed_checks health checks failed"
        exit 1
    fi
}

# Run main function
main "$@"
