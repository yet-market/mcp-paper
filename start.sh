#!/bin/bash
# Start MCP Paper Server locally

set -e

cd server

if [ ! -f "venv/bin/activate" ]; then
    echo "❌ Virtual environment not found. Run ./install.sh first."
    exit 1
fi

source venv/bin/activate

if [ "$1" = "stdio" ]; then
    echo "🚀 Starting stdio server..."
    python server.py
elif [ "$1" = "http" ]; then
    echo "🚀 Starting HTTP server..."
    python server.py --transport streamable-http --host localhost --port 8000
else
    echo "🚀 Starting HTTP server (default)..."
    echo "🌐 Server will be available at: http://localhost:8000/mcp/"
    echo "Use './start.sh stdio' for stdio mode"
    python server.py --transport streamable-http --host localhost --port 8000
fi