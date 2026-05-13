#!/usr/bin/env bash
# Setup script for macOS / Linux
# Usage: bash scripts/setup.sh

set -e
cd "$(dirname "$0")/.."

echo -e "\033[36m=== into-the-git Setup (Unix) ===\033[0m"

# Check Python
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo -e "\033[31m[FAIL] Python not found. Install Python 3.9+\033[0m"
    exit 1
fi
echo -e "\033[32m[OK] $($PYTHON --version)\033[0m"

# Check Git
if command -v git &>/dev/null; then
    echo -e "\033[32m[OK] $(git --version)\033[0m"
else
    echo -e "\033[31m[FAIL] Git not found\033[0m"
    exit 1
fi

# Create virtualenv
if [ ! -d "venv" ]; then
    echo -e "\033[33mCreating virtual environment...\033[0m"
    $PYTHON -m venv venv
    echo -e "\033[32m[OK] Virtualenv created\033[0m"
else
    echo -e "\033[33m[SKIP] Virtualenv already exists\033[0m"
fi

# Activate and install
echo -e "\033[33mInstalling dependencies...\033[0m"
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -e ".[dev]" --quiet
echo -e "\033[32m[OK] Dependencies installed\033[0m"

# Create data directories
mkdir -p data/repos data/reports

# Verify
echo -e "\033[33mRunning tests...\033[0m"
python -m unittest discover tests -v 2>&1 | tail -2

echo ""
echo -e "\033[36m=== Setup Complete ===\033[0m"
echo ""
echo -e "Activate the virtualenv:  \033[37msource venv/bin/activate\033[0m"
echo -e "Start the app:            \033[37mmake run\033[0m"
echo -e "Open the dashboard:       \033[37mhttp://localhost:5000\033[0m"
