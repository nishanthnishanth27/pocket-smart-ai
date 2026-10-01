#!/usr/bin/env bash

echo "=========================================="
echo "          PocketSmart AI"
echo "=========================================="

if [ ! -d ".venv" ]; then
    echo "Virtual environment not found."
    echo "Create it using:"
    echo "python3 -m venv .venv"
    exit 1
fi

source .venv/bin/activate

echo "Starting PocketSmart AI..."

uvicorn app.main:app --reload
