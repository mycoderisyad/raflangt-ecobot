#!/bin/bash

# EcoBot Production Deployment Script

set -e

echo "Starting EcoBot deployment..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.example to .env and configure your settings."
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run basic validation
echo "Running basic validation..."
python3 -c "import flask, requests, openai, PIL; print('All dependencies installed correctly')"

# Clean up any cache files
echo "Cleaning up cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Create logs directory if it doesn't exist
mkdir -p logs

echo "✅ Deployment preparation complete!"
echo ""
echo "To start EcoBot:"
echo "  Development: python3 main.py"
echo "  Production:  python3 main.py --production"
echo ""
echo "Production with Gunicorn:"
echo "  gunicorn -w 4 -b 0.0.0.0:8000 'main:create_app(\"production\")'"
