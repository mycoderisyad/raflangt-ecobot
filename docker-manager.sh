#!/bin/bash

# EcoBot Docker Management Script
# Usage: ./docker-manager.sh [command] [environment]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default environment
ENVIRONMENT=${2:-production}

# Set port based on environment
if [ "$ENVIRONMENT" = "development" ]; then
    export PORT=5000
    export ENVIRONMENT=development
else
    export PORT=8000
    export ENVIRONMENT=production
fi

print_header() {
    echo -e "${BLUE}🚀 EcoBot Docker Manager${NC}"
    echo -e "${BLUE}========================${NC}"
    echo ""
}

print_usage() {
    print_header
    echo "Usage: ./docker-manager.sh [command] [environment]"
    echo ""
    echo "Commands:"
    echo -e "  ${GREEN}build${NC}       - Build EcoBot Docker image"
    echo -e "  ${GREEN}start${NC}       - Start EcoBot container"
    echo -e "  ${GREEN}stop${NC}        - Stop EcoBot container"
    echo -e "  ${GREEN}restart${NC}     - Restart EcoBot container"
    echo -e "  ${GREEN}logs${NC}        - Show container logs"
    echo -e "  ${GREEN}logs-live${NC}   - Show live container logs"
    echo -e "  ${GREEN}status${NC}      - Show container status"
    echo -e "  ${GREEN}shell${NC}       - Open shell in container"
    echo -e "  ${GREEN}health${NC}      - Check container health"
    echo -e "  ${GREEN}clean${NC}       - Clean up containers and images"
    echo -e "  ${GREEN}rebuild${NC}     - Clean build and start"
    echo ""
    echo "Environments:"
    echo -e "  ${YELLOW}production${NC}  - Production mode (port 8000)"
    echo -e "  ${YELLOW}development${NC} - Development mode (port 5000)"
    echo ""
    echo "Examples:"
    echo "  ./docker-manager.sh start production"
    echo "  ./docker-manager.sh start development"
    echo "  ./docker-manager.sh logs"
    echo "  ./docker-manager.sh rebuild development"
}

build_image() {
    echo -e "${BLUE}🔨 Building EcoBot image for ${ENVIRONMENT}...${NC}"
    docker-compose build --no-cache
    echo -e "${GREEN}✅ Build completed!${NC}"
}

start_container() {
    echo -e "${BLUE}🚀 Starting EcoBot in ${ENVIRONMENT} mode on port ${PORT}...${NC}"
    docker-compose up -d
    
    # Wait for container to be ready
    echo -e "${YELLOW}⏳ Waiting for EcoBot to be ready...${NC}"
    sleep 10
    
    # Check health
    if check_health_silent; then
        echo -e "${GREEN}✅ EcoBot started successfully!${NC}"
        echo -e "${GREEN}🌐 EcoBot running at: http://localhost:${PORT}${NC}"
        echo -e "${GREEN}💚 Health check: http://localhost:${PORT}/health${NC}"
    else
        echo -e "${RED}❌ EcoBot failed to start properly${NC}"
        echo -e "${YELLOW}📋 Check logs with: ./docker-manager.sh logs${NC}"
    fi
}

stop_container() {
    echo -e "${BLUE}🛑 Stopping EcoBot...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ EcoBot stopped!${NC}"
}

restart_container() {
    echo -e "${BLUE}🔄 Restarting EcoBot...${NC}"
    stop_container
    sleep 2
    start_container
}

show_logs() {
    echo -e "${BLUE}📋 EcoBot logs:${NC}"
    docker-compose logs --tail=50
}

show_logs_live() {
    echo -e "${BLUE}📋 EcoBot live logs (Ctrl+C to exit):${NC}"
    docker-compose logs -f
}

show_status() {
    echo -e "${BLUE}📊 EcoBot container status:${NC}"
    docker-compose ps
    echo ""
    echo -e "${BLUE}🐳 Docker images:${NC}"
    docker images | grep ecobot || echo "No EcoBot images found"
}

open_shell() {
    echo -e "${BLUE}🐚 Opening shell in EcoBot container...${NC}"
    docker-compose exec ecobot /bin/bash
}

check_health_silent() {
    curl -s -f "http://localhost:${PORT}/health" > /dev/null 2>&1
    return $?
}

check_health() {
    echo -e "${BLUE}🏥 Checking EcoBot health...${NC}"
    
    if check_health_silent; then
        echo -e "${GREEN}✅ EcoBot is healthy!${NC}"
        echo -e "${GREEN}🌐 Available at: http://localhost:${PORT}${NC}"
        
        # Get health response
        health_response=$(curl -s "http://localhost:${PORT}/health" 2>/dev/null || echo "Could not get detailed health info")
        echo -e "${BLUE}📋 Health response:${NC} $health_response"
    else
        echo -e "${RED}❌ EcoBot is not responding${NC}"
        echo -e "${YELLOW}💡 Try: ./docker-manager.sh logs${NC}"
        exit 1
    fi
}

clean_up() {
    echo -e "${BLUE}🧹 Cleaning up EcoBot containers and images...${NC}"
    
    # Stop and remove containers
    docker-compose down --rmi all --volumes --remove-orphans 2>/dev/null || true
    
    # Remove dangling images
    docker image prune -f 2>/dev/null || true
    
    echo -e "${GREEN}✅ Cleanup completed!${NC}"
}

rebuild_all() {
    echo -e "${BLUE}🔄 Rebuilding EcoBot from scratch...${NC}"
    clean_up
    build_image
    start_container
}

# Main command handling
case "$1" in
    "build")
        build_image
        ;;
    "start")
        start_container
        ;;
    "stop")
        stop_container
        ;;
    "restart")
        restart_container
        ;;
    "logs")
        show_logs
        ;;
    "logs-live")
        show_logs_live
        ;;
    "status")
        show_status
        ;;
    "shell")
        open_shell
        ;;
    "health")
        check_health
        ;;
    "clean")
        clean_up
        ;;
    "rebuild")
        rebuild_all
        ;;
    *)
        print_usage
        exit 1
        ;;
esac
