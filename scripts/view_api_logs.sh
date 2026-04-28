#!/bin/bash
# Script to view API logs with various filtering options

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

show_help() {
    echo "API Log Viewer"
    echo "=============="
    echo ""
    echo "Usage: $0 [option]"
    echo ""
    echo "Options:"
    echo "  all              - Show all logs (default)"
    echo "  no-health        - Exclude health check logs"
    echo "  api-only         - Show only API endpoint calls (exclude /, /health)"
    echo "  post-only        - Show only POST requests"
    echo "  errors           - Show only errors"
    echo "  gemini           - Show only Gemini API calls"
    echo "  slow             - Show requests taking >1 second"
    echo "  ui-requests      - Show requests from web browser"
    echo "  last-N           - Show last N lines (e.g., last-50)"
    echo "  help             - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 no-health     # View logs without healthchecks"
    echo "  $0 api-only      # View only API calls"
    echo "  $0 gemini        # View Gemini API interactions"
}

case "${1:-all}" in
    all)
        echo -e "${BLUE}📊 Showing all logs...${NC}"
        docker-compose logs -f pdf-compliance-api
        ;;
    
    no-health)
        echo -e "${BLUE}📊 Showing logs (excluding health checks)...${NC}"
        docker-compose logs -f pdf-compliance-api | grep -v "/health"
        ;;
    
    api-only)
        echo -e "${BLUE}📊 Showing API endpoint calls only...${NC}"
        docker-compose logs -f pdf-compliance-api | grep -E "📥 INCOMING REQUEST" | grep -v "/health" | grep -v '"path": "/"'
        ;;
    
    post-only)
        echo -e "${BLUE}📊 Showing POST requests only...${NC}"
        docker-compose logs -f pdf-compliance-api | grep -E "📥 INCOMING REQUEST" | grep '"method": "POST"'
        ;;
    
    errors)
        echo -e "${YELLOW}⚠️  Showing errors only...${NC}"
        docker-compose logs -f pdf-compliance-api | grep -E "ERROR|💥|❌|Exception"
        ;;
    
    gemini)
        echo -e "${GREEN}🤖 Showing Gemini API calls...${NC}"
        docker-compose logs -f pdf-compliance-api | grep -E "🌐|GEMINI|Gemini"
        ;;
    
    slow)
        echo -e "${YELLOW}🐌 Showing slow requests (>1000ms)...${NC}"
        docker-compose logs -f pdf-compliance-api | grep "duration_ms" | awk -F'"duration_ms": ' '{print $2}' | awk -F',' '{if ($1 > 1000) print $0}'
        ;;
    
    ui-requests)
        echo -e "${BLUE}🌐 Showing web browser requests...${NC}"
        docker-compose logs -f pdf-compliance-api | grep -E "Mozilla|Chrome|Safari|Firefox"
        ;;
    
    last-*)
        NUM="${1#last-}"
        echo -e "${BLUE}📊 Showing last $NUM lines...${NC}"
        docker-compose logs --tail "$NUM" pdf-compliance-api
        ;;
    
    help|--help|-h)
        show_help
        ;;
    
    *)
        echo -e "${YELLOW}Unknown option: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac

