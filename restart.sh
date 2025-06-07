#!/bin/bash
# Restart MCP Paper Server

set -e

echo "🔄 Restarting MCP Paper Server..."

# Stop the server first
echo "⏹️  Stopping server..."
./stop.sh

# Wait a moment for clean shutdown
sleep 2

# Start the server
echo "🚀 Starting server..."
./start.sh "$@"