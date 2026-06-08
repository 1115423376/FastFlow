#!/bin/bash
set -euo pipefail

# FastFlow Nexus Startup Script
# Usage: ./start.sh [OPTIONS]
#   -f, --foreground  Run in foreground (default)
#   -d, --daemon      Run in background (daemon mode)
#   -s, --stop        Stop daemon
#   -r, --restart     Restart daemon
#   -h, --help        Show this help

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$SCRIPT_DIR/.venv"
REQUIREMENTS="$SCRIPT_DIR/requirements.txt"
HASH_FILE="$SCRIPT_DIR/.req_hash"
PID_FILE="$SCRIPT_DIR/.nexus.pid"
LOG_DIR="$SCRIPT_DIR/logs"
HEALTH_URL="http://localhost:8969/fastflow/nexus/v1/health"
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=10

check_python_version() {
    local version
    version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    local major="${version%%.*}"
    local minor="${version##*.}"
    
    if [[ "$major" -lt "$MIN_PYTHON_MAJOR" ]] || [[ "$major" -eq "$MIN_PYTHON_MAJOR" && "$minor" -lt "$MIN_PYTHON_MINOR" ]]; then
        echo "❌ Python $MIN_PYTHON_MAJOR.$MIN_PYTHON_MINOR+ required, found $version"
        exit 1
    fi
    echo "✅ Python $version detected"
}

setup_venv() {
    if [[ ! -f "$VENV_DIR/bin/activate" ]]; then
        echo "📦 Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi
    source "$VENV_DIR/bin/activate"
    echo "✅ Virtual environment activated"
}

install_deps() {
    local current_hash stored_hash
    current_hash=$(sha256sum "$REQUIREMENTS" | cut -d' ' -f1)
    
    if [[ -f "$HASH_FILE" ]]; then
        stored_hash=$(cat "$HASH_FILE")
        if [[ "$current_hash" == "$stored_hash" ]]; then
            echo "✅ Dependencies up to date"
            return 0
        fi
    fi
    
    echo "📥 Installing dependencies..."
    pip install --upgrade pip --quiet
    pip install -r "$REQUIREMENTS"
    echo "$current_hash" > "$HASH_FILE"
    echo "✅ Dependencies installed"
}

set_pythonpath() {
    export PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH:-}"
    echo "📁 PYTHONPATH=$PYTHONPATH"
}

start_foreground() {
    echo "🚀 Starting Nexus in foreground..."
    echo "   Health check: curl $HEALTH_URL"
    echo "   Press Ctrl+C to stop"
    exec python -m nexus.main
}

start_daemon() {
    if [[ -f "$PID_FILE" ]]; then
        local pid
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            echo "⚠️  Nexus already running (PID: $pid)"
            exit 1
        fi
    fi
    
    mkdir -p "$LOG_DIR"
    nohup python -m nexus.main > "$LOG_DIR/nexus.log" 2>&1 &
    echo $! > "$PID_FILE"
    echo "✅ Daemon started (PID: $(cat "$PID_FILE"))"
    echo "📋 Logs: $LOG_DIR/nexus.log"
    health_check
}

stop_daemon() {
    if [[ ! -f "$PID_FILE" ]]; then
        echo "ℹ️  No PID file found"
        return 0
    fi
    
    local pid
    pid=$(cat "$PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
        echo "⏹️  Stopping PID $pid..."
        kill "$pid"
        local timeout=5
        while [[ $timeout -gt 0 ]] && kill -0 "$pid" 2>/dev/null; do
            sleep 1
            ((timeout--))
        done
        if kill -0 "$pid" 2>/dev/null; then
            echo "⚠️  Force killing PID $pid..."
            kill -9 "$pid"
        fi
        echo "✅ Stopped"
    else
        echo "⚠️  Process $pid not running"
    fi
    rm -f "$PID_FILE"
}

health_check() {
    echo "🔍 Waiting for Nexus to start..."
    local attempts=30
    while [[ $attempts -gt 0 ]]; do
        if curl -sf "$HEALTH_URL" >/dev/null 2>&1; then
            echo "✅ Nexus is healthy"
            return 0
        fi
        sleep 1
        ((attempts--))
    done
    echo "❌ Health check timed out"
    return 1
}

show_help() {
    echo "FastFlow Nexus Startup Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -f, --foreground  Run in foreground (default)"
    echo "  -d, --daemon      Run in background (daemon mode)"
    echo "  -s, --stop        Stop daemon"
    echo "  -r, --restart     Restart daemon"
    echo "  -h, --help        Show this help"
    echo ""
    echo "Examples:"
    echo "  $0                # Start in foreground"
    echo "  $0 --daemon       # Start in background"
    echo "  $0 --stop         # Stop daemon"
}

START_MODE="foreground"

case "${1:-}" in
    -f|--foreground)  START_MODE="foreground" ;;
    -d|--daemon)      START_MODE="daemon" ;;
    -s|--stop)        stop_daemon; exit 0 ;;
    -r|--restart)     stop_daemon; sleep 1; START_MODE="daemon" ;;
    -h|--help)        show_help; exit 0 ;;
    "")               START_MODE="foreground" ;;
    *)                echo "Unknown option: $1"; show_help; exit 1 ;;
esac

check_python_version
setup_venv
install_deps
set_pythonpath

if [[ "$START_MODE" == "daemon" ]]; then
    start_daemon
else
    start_foreground
fi