#!/bin/bash
# View logs from different components

echo "📋 Polyglot RAG Logs Viewer"
echo "=========================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if logs directory exists
if [ ! -d "logs" ]; then
    echo -e "${YELLOW}No logs directory found. Run the application first.${NC}"
    exit 1
fi

# List available logs
echo -e "\n${BLUE}Available logs:${NC}"
ls -la logs/*.log 2>/dev/null || echo "No log files found"

# Function to tail a specific log
view_log() {
    local log_file=$1
    if [ -f "$log_file" ]; then
        echo -e "\n${GREEN}Viewing: $log_file${NC}"
        echo "Press Ctrl+C to stop"
        tail -f "$log_file"
    else
        echo -e "${YELLOW}Log file not found: $log_file${NC}"
    fi
}

# Menu
echo -e "\n${BLUE}Choose an option:${NC}"
echo "1) View all logs (combined)"
echo "2) View orchestrator.log"
echo "3) View gradio_app.log" 
echo "4) View flight_api.log"
echo "5) View flight_agent.log"
echo "6) View voice_agent.log"
echo "7) View specific log file"
echo "8) Clear all logs"
echo "q) Quit"

read -p "Enter choice: " choice

case $choice in
    1)
        echo -e "\n${GREEN}Viewing all logs (combined)${NC}"
        tail -f logs/*.log
        ;;
    2)
        view_log "logs/orchestrator.log"
        ;;
    3)
        view_log "logs/gradio_app.log"
        ;;
    4)
        view_log "logs/flight_api.log"
        ;;
    5)
        view_log "logs/flight_agent.log"
        ;;
    6)
        view_log "logs/voice_agent.log"
        ;;
    7)
        read -p "Enter log filename (e.g., gradio_app.log): " filename
        view_log "logs/$filename"
        ;;
    8)
        read -p "Are you sure you want to clear all logs? (y/N): " confirm
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            rm -f logs/*.log
            echo -e "${GREEN}All logs cleared${NC}"
        fi
        ;;
    q)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo -e "${YELLOW}Invalid choice${NC}"
        exit 1
        ;;
esac