#!/bin/bash
# Script to enable and test API logging in Docker Compose

set -e

echo "🔧 API Logging Configuration Script"
echo "===================================="
echo ""

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: docker-compose is not installed"
    exit 1
fi

# Function to update .env file
update_env_file() {
    local env_file=".env"
    
    if [ ! -f "$env_file" ]; then
        echo "📝 Creating .env file from .env.example..."
        cp .env.example "$env_file"
    fi
    
    # Update or add ENABLE_API_LOGGING
    if grep -q "ENABLE_API_LOGGING" "$env_file"; then
        sed -i 's/ENABLE_API_LOGGING=.*/ENABLE_API_LOGGING=true/' "$env_file"
    else
        echo "ENABLE_API_LOGGING=true" >> "$env_file"
    fi
    
    # Update or add ENABLE_VERBOSE_LOGGING
    if grep -q "ENABLE_VERBOSE_LOGGING" "$env_file"; then
        sed -i 's/ENABLE_VERBOSE_LOGGING=.*/ENABLE_VERBOSE_LOGGING=false/' "$env_file"
    else
        echo "ENABLE_VERBOSE_LOGGING=false" >> "$env_file"
    fi
    
    echo "✅ Updated $env_file with logging configuration"
}

# Function to show current configuration
show_config() {
    echo ""
    echo "📋 Current Configuration:"
    echo "------------------------"
    if [ -f ".env" ]; then
        grep -E "ENABLE_API_LOGGING|ENABLE_VERBOSE_LOGGING" .env || echo "No logging config found"
    else
        echo "No .env file found"
    fi
    echo ""
}

# Function to restart services
restart_services() {
    echo "🔄 Restarting Docker Compose services..."
    docker-compose down
    docker-compose up -d
    echo "✅ Services restarted"
    echo ""
}

# Function to show log commands
show_log_commands() {
    echo "📊 Useful Log Commands:"
    echo "----------------------"
    echo ""
    echo "1. View all logs in real-time:"
    echo "   docker-compose logs -f pdf-compliance-api"
    echo ""
    echo "2. View only API-related logs:"
    echo "   docker-compose logs -f pdf-compliance-api | grep -E 'INCOMING|OUTGOING|GEMINI'"
    echo ""
    echo "3. View incoming requests only:"
    echo "   docker-compose logs pdf-compliance-api | grep '📥 INCOMING REQUEST'"
    echo ""
    echo "4. View Gemini API calls:"
    echo "   docker-compose logs pdf-compliance-api | grep '🌐 GEMINI API'"
    echo ""
    echo "5. Export logs to file:"
    echo "   docker-compose logs pdf-compliance-api > api_logs.txt"
    echo ""
    echo "6. View last 100 lines:"
    echo "   docker-compose logs --tail 100 pdf-compliance-api"
    echo ""
}

# Function to test API logging
test_logging() {
    echo "🧪 Testing API Logging..."
    echo "------------------------"
    echo ""
    
    # Wait for service to be ready
    echo "⏳ Waiting for service to be ready..."
    sleep 5
    
    # Test health endpoint
    echo "📡 Testing health endpoint..."
    curl -s http://localhost:8000/health > /dev/null
    
    echo "✅ Test request sent"
    echo ""
    echo "📋 Recent logs (last 20 lines):"
    echo "--------------------------------"
    docker-compose logs --tail 20 pdf-compliance-api
    echo ""
}

# Main menu
show_menu() {
    echo ""
    echo "Choose an option:"
    echo "1) Enable API logging (standard mode)"
    echo "2) Enable verbose logging (debug mode)"
    echo "3) Disable API logging"
    echo "4) Show current configuration"
    echo "5) Restart services"
    echo "6) Test logging with sample request"
    echo "7) Show log viewing commands"
    echo "8) View live logs"
    echo "9) Exit"
    echo ""
    read -p "Enter choice [1-9]: " choice
    
    case $choice in
        1)
            update_env_file
            restart_services
            show_config
            echo "✅ Standard API logging enabled"
            ;;
        2)
            if [ ! -f ".env" ]; then
                cp .env.example .env
            fi
            sed -i 's/ENABLE_API_LOGGING=.*/ENABLE_API_LOGGING=true/' .env
            sed -i 's/ENABLE_VERBOSE_LOGGING=.*/ENABLE_VERBOSE_LOGGING=true/' .env
            restart_services
            show_config
            echo "✅ Verbose logging enabled (includes full request/response bodies)"
            echo "⚠️  Warning: Not recommended for production!"
            ;;
        3)
            if [ ! -f ".env" ]; then
                cp .env.example .env
            fi
            sed -i 's/ENABLE_API_LOGGING=.*/ENABLE_API_LOGGING=false/' .env
            sed -i 's/ENABLE_VERBOSE_LOGGING=.*/ENABLE_VERBOSE_LOGGING=false/' .env
            restart_services
            show_config
            echo "✅ API logging disabled"
            ;;
        4)
            show_config
            ;;
        5)
            restart_services
            ;;
        6)
            test_logging
            ;;
        7)
            show_log_commands
            ;;
        8)
            echo "📊 Viewing live logs (Press Ctrl+C to exit)..."
            echo ""
            docker-compose logs -f pdf-compliance-api
            ;;
        9)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid choice"
            ;;
    esac
    
    # Show menu again
    show_menu
}

# Start the script
show_menu

