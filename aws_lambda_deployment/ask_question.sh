#!/bin/bash

# Simple wrapper script for asking questions
# Usage: ./ask_question.sh "Your question here" [provider]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/interactive_client.py"
VENV_DIR="$SCRIPT_DIR/client_venv"

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "❌ Error: interactive_client.py not found"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "❌ Error: Virtual environment not found. Run: python3 -m venv client_venv && source client_venv/bin/activate && pip install requests"
    exit 1
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Get question from command line or prompt
if [ -n "$1" ]; then
    QUESTION="$1"
    PROVIDER="${2:-anthropic}"
    python3 "$PYTHON_SCRIPT" --question "$QUESTION" --provider "$PROVIDER"
else
    echo "🏛️  Luxembourg Legal Assistant - Quick Question"
    echo "=============================================="
    echo ""
    echo "Available providers:"
    echo "  • anthropic (Claude) - Most accurate, slower"
    echo "  • openai (GPT-4.1) - Fast, cheap, good quality"
    echo "  • groq (Llama) - Fastest, good for simple questions"
    echo ""
    
    # Interactive mode
    python3 "$PYTHON_SCRIPT"
fi