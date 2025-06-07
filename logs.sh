#!/bin/bash
# View MCP Paper Server logs

# Check if we're in a systemd environment
if command -v systemctl &> /dev/null && [ -f /etc/systemd/system/mcp-sparql-http.service ]; then
    if [ "$1" = "stdio" ]; then
        echo "📜 Viewing stdio service logs (Ctrl+C to exit):"
        sudo journalctl -u mcp-sparql -f
    elif [ "$1" = "http" ]; then
        echo "📜 Viewing HTTP service logs (Ctrl+C to exit):"
        sudo journalctl -u mcp-sparql-http -f
    else
        echo "📜 Viewing HTTP service logs (Ctrl+C to exit):"
        echo "Use './logs.sh stdio' for stdio service logs"
        echo
        sudo journalctl -u mcp-sparql-http -f
    fi
else
    echo "📜 Local Development Mode"
    echo "Logs will appear in the terminal where you started the server"
    echo
    echo "To start server with logs:"
    echo "  ./start.sh [stdio|http]"
    echo
    echo "For more detailed logs, edit server/server.py and set logging level to DEBUG"
fi