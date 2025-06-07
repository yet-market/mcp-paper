#!/bin/bash
# Stop MCP Paper Server services

set -e

print_status() {
    echo -e "\033[0;32m[INFO]\033[0m $1"
}

# Check if we're in a systemd environment
if command -v systemctl &> /dev/null && [ -f /etc/systemd/system/mcp-sparql-http.service ]; then
    if [ "$1" = "stdio" ]; then
        print_status "Stopping stdio service..."
        sudo systemctl stop mcp-sparql
        echo "✅ stdio service stopped"
    elif [ "$1" = "http" ]; then
        print_status "Stopping HTTP service..."
        sudo systemctl stop mcp-sparql-http
        echo "✅ HTTP service stopped"
    else
        print_status "Stopping all services..."
        sudo systemctl stop mcp-sparql-http 2>/dev/null || true
        sudo systemctl stop mcp-sparql 2>/dev/null || true
        echo "✅ All services stopped"
    fi
else
    print_status "Stopping local server processes..."
    # Kill any running server.py processes
    pkill -f "python.*server.py" 2>/dev/null || true
    echo "✅ Local server processes stopped"
fi