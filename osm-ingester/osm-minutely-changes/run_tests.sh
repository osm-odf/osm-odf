#!/bin/bash
set -e  # Exit on error

# Change to script directory
cd "$(dirname "$0")"

# Check if virtual environment exists, create if not
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install test requirements
echo "Installing test requirements..."
pip install -r test_requirements.txt

# Run tests
echo "Running tests..."
if [ "$1" == "--coverage" ]; then
    python -m pytest tests/ --cov=. --cov-report=term-missing
else
    python -m pytest tests/
fi

echo "Tests completed."