#!/bin/bash
# Installation script for MCP Paper Server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default installation directory
INSTALL_DIR="/opt/mcp-sparql"
SERVICE_USER="mcp-sparql"

# Print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root for systemd service installation
if [ "$EUID" -ne 0 ]; then
    print_warning "For full installation with systemd service, please run as root."
    print_warning "Continuing with local installation only..."
    INSTALL_SYSTEMD=false
else
    INSTALL_SYSTEMD=true
fi

# Check Python version
print_status "Checking Python version..."
if ! python3 --version | grep -E "Python 3\.[8-9]|Python 3\.1[0-9]" > /dev/null; then
    print_error "Python 3.8+ is required"
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is required but not installed"
    exit 1
fi

# If installing system-wide, create installation directory and user
if [ "$INSTALL_SYSTEMD" = true ]; then
    print_status "Setting up system installation..."
    
    # Create installation directory
    mkdir -p "$INSTALL_DIR"
    
    # Create service user if it doesn't exist
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd --system --shell /bin/false --home-dir "$INSTALL_DIR" --create-home "$SERVICE_USER"
        print_status "Created user: $SERVICE_USER"
    fi
    
    # Copy project files to installation directory
    cp -r . "$INSTALL_DIR/"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    
    cd "$INSTALL_DIR"
fi

# Create virtual environment in server directory
cd server
print_status "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt

# Go back to root directory
cd ..

# If running as root, install systemd service
if [ "$INSTALL_SYSTEMD" = true ]; then
    print_status "Installing systemd service..."
    
    # Create log directory
    mkdir -p /var/log/mcp-sparql
    chown "$SERVICE_USER:$SERVICE_USER" /var/log/mcp-sparql
    
    # Create config directory
    mkdir -p /etc/mcp-sparql
    
    # Create a default environment file
    cat > /etc/mcp-sparql/env <<EOF
# MCP Paper Server environment configuration

# Transport configuration  
MCP_TRANSPORT=streamable-http
MCP_HOST=localhost
MCP_PORT=8000

# SPARQL endpoint URL (required)
SPARQL_ENDPOINT=https://data.legilux.public.lu/sparqlendpoint

# Request timeout in seconds
SPARQL_TIMEOUT=30

# Maximum number of results
SPARQL_MAX_RESULTS=1000

# Cache configuration
SPARQL_CACHE_ENABLED=true
SPARQL_CACHE_TTL=300
SPARQL_CACHE_MAX_SIZE=100
SPARQL_CACHE_STRATEGY=lru
EOF
    
    # Create systemd service file
    cat > /etc/systemd/system/mcp-sparql.service <<EOF
[Unit]
Description=MCP SPARQL Server
After=network.target
Documentation=https://github.com/yet-market/mcp-paper

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR/server
EnvironmentFile=-/etc/mcp-sparql/env
ExecStart=$INSTALL_DIR/server/venv/bin/python server.py --transport streamable-http --host localhost --port 8080 --endpoint https://data.legilux.public.lu/sparqlendpoint
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3
TimeoutStopSec=10

# Sandboxing
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/mcp-sparql
PrivateTmp=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

# Limits
LimitNOFILE=65536
LimitNPROC=32768

[Install]
WantedBy=multi-user.target
EOF

    # Create HTTP service variant
    cat > /etc/systemd/system/mcp-sparql-http.service <<EOF
[Unit]
Description=MCP SPARQL Server (HTTP)
After=network.target
Documentation=https://github.com/yet-market/mcp-paper

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR/server
EnvironmentFile=-/etc/mcp-sparql/env
ExecStart=$INSTALL_DIR/server/venv/bin/python server.py --transport streamable-http --host localhost --port 8000 --endpoint https://data.legilux.public.lu/sparqlendpoint
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3
TimeoutStopSec=10

# Sandboxing
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/mcp-sparql
PrivateTmp=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

# Limits
LimitNOFILE=65536
LimitNPROC=32768

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    systemctl daemon-reload
    
    # Create management scripts
    print_status "Creating management scripts..."
    
    # Create start script
    cat > "$INSTALL_DIR/start.sh" <<'EOF'
#!/bin/bash
# Start MCP SPARQL Server services

set -e

print_status() {
    echo -e "\033[0;32m[INFO]\033[0m $1"
}

if [ "$1" = "stdio" ]; then
    print_status "Starting stdio service..."
    sudo systemctl start mcp-sparql
    sudo systemctl enable mcp-sparql
    echo "✅ stdio service started"
elif [ "$1" = "http" ]; then
    print_status "Starting HTTP service..."
    sudo systemctl start mcp-sparql-http
    sudo systemctl enable mcp-sparql-http
    echo "✅ HTTP service started at http://localhost:8000/mcp/"
else
    print_status "Starting HTTP service (default)..."
    sudo systemctl start mcp-sparql-http
    sudo systemctl enable mcp-sparql-http
    echo "✅ HTTP service started at http://localhost:8000/mcp/"
    echo "Use './start.sh stdio' to start stdio service instead"
fi
EOF

    # Create stop script
    cat > "$INSTALL_DIR/stop.sh" <<'EOF'
#!/bin/bash
# Stop MCP SPARQL Server services

set -e

print_status() {
    echo -e "\033[0;32m[INFO]\033[0m $1"
}

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
EOF

    # Create restart script
    cat > "$INSTALL_DIR/restart.sh" <<'EOF'
#!/bin/bash
# Restart MCP SPARQL Server

set -e

echo "🔄 Restarting MCP SPARQL Server..."

# Stop the server first
echo "⏹️  Stopping server..."
./stop.sh

# Wait a moment for clean shutdown
sleep 2

# Start the server
echo "🚀 Starting server..."
./start.sh "$@"
EOF

    # Create status script
    cat > "$INSTALL_DIR/status.sh" <<'EOF'
#!/bin/bash
# Check MCP SPARQL Server service status

echo "=== MCP SPARQL Server Status ==="
echo

echo "📋 Available Services:"
echo "  - mcp-sparql.service      (stdio transport)"
echo "  - mcp-sparql-http.service (HTTP transport)"
echo

echo "🔍 Service Status:"
for service in mcp-sparql mcp-sparql-http; do
    if sudo systemctl is-active --quiet $service; then
        status="✅ RUNNING"
    else
        status="❌ STOPPED"
    fi
    echo "  $service: $status"
done

echo

if sudo systemctl is-active --quiet mcp-sparql-http; then
    echo "🌐 HTTP Service Details:"
    sudo systemctl status mcp-sparql-http --no-pager -l | head -10
    echo
    echo "📍 MCP Endpoint: http://localhost:8000/mcp/"
fi

echo "📊 Quick Commands:"
echo "  ./start.sh [stdio|http]  - Start service"
echo "  ./stop.sh [stdio|http]   - Stop service"
echo "  ./restart.sh [stdio|http] - Restart service"
echo "  ./logs.sh [stdio|http]   - View logs"
echo "  sudo systemctl restart mcp-sparql-http"
EOF

    # Create logs script
    cat > "$INSTALL_DIR/logs.sh" <<'EOF'
#!/bin/bash
# View MCP SPARQL Server logs

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
EOF
    
    # Make scripts executable
    chmod +x "$INSTALL_DIR/start.sh"
    chmod +x "$INSTALL_DIR/stop.sh"
    chmod +x "$INSTALL_DIR/restart.sh"
    chmod +x "$INSTALL_DIR/status.sh"
    chmod +x "$INSTALL_DIR/logs.sh"
    
    print_status "Systemd services installed successfully!"
    
    # Stop any running services before starting
    print_status "Stopping existing services..."
    systemctl stop mcp-sparql 2>/dev/null || true
    systemctl stop mcp-sparql-http 2>/dev/null || true
    
    # Start and enable the HTTP service (most common for nginx integration)
    print_status "Starting MCP SPARQL HTTP service..."
    systemctl start mcp-sparql-http
    systemctl enable mcp-sparql-http
    
    # Wait a moment for service to start
    sleep 2
    
    # Check service status
    if systemctl is-active --quiet mcp-sparql-http; then
        print_status "✅ HTTP service started successfully!"
        echo
        echo "🌐 MCP Server is running at: http://localhost:8000/mcp/"
        echo
        print_status "Service status:"
        systemctl status mcp-sparql-http --no-pager -l
        
        # Run basic connectivity test
        echo
        print_status "Running connectivity test..."
        if timeout 5 curl -s http://localhost:8000/mcp/ > /dev/null 2>&1; then
            print_status "✅ Server connectivity test passed!"
        else
            print_warning "⚠️  Server connectivity test failed (may still be starting)"
        fi
    else
        print_error "❌ HTTP service failed to start!"
        echo "Check logs with: journalctl -u mcp-sparql-http -f"
        exit 1
    fi
    
    echo
    echo "📋 Available services:"
    echo "  - mcp-sparql.service      (stdio transport)"
    echo "  - mcp-sparql-http.service (HTTP transport for nginx) ✅ RUNNING"
    echo
    echo "🔧 Configuration:"
    echo "  Edit: /etc/mcp-sparql/env"
    echo
    echo "📜 Management scripts created:"
    echo "  ./start.sh    - Start services"
    echo "  ./stop.sh     - Stop services" 
    echo "  ./restart.sh  - Restart services"
    echo "  ./status.sh   - Check service status"
    echo "  ./logs.sh     - View logs"
    echo
    echo "📊 Quick commands:"
    echo "  journalctl -u mcp-sparql-http -f     # View HTTP service logs"
    echo "  systemctl restart mcp-sparql-http    # Restart HTTP service"
    
else
    print_status "Creating local management scripts..."
    
    # Create local start script
    cat > start.sh <<'EOF'
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
EOF

    # Create local stop script
    cat > stop.sh <<'EOF'
#!/bin/bash
# Stop MCP Paper Server locally

set -e

print_status() {
    echo -e "\033[0;32m[INFO]\033[0m $1"
}

print_status "Stopping local server processes..."
# Kill any running server.py processes
pkill -f "python.*server.py" 2>/dev/null || true
echo "✅ Local server processes stopped"
EOF

    # Create local restart script
    cat > restart.sh <<'EOF'
#!/bin/bash
# Restart MCP Paper Server locally

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
EOF

    chmod +x start.sh
    chmod +x stop.sh
    chmod +x restart.sh
    
    print_status "Local installation complete!"
    echo
    echo "📜 Management scripts created:"
    echo "  ./start.sh [stdio|http]  - Start server locally"
    echo "  ./stop.sh                - Stop server locally"
    echo "  ./restart.sh [stdio|http] - Restart server locally"
    echo
    echo "🚀 Quick start:"
    echo "  ./start.sh http    # Start HTTP server"
    echo "  ./start.sh stdio   # Start stdio server"
    echo
    echo "📝 Manual commands:"
    echo "  cd server && source venv/bin/activate"
    echo "  python server.py"
fi

print_status "Installation completed successfully!"