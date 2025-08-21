#!/bin/bash

set -e

# Set defaults if not provided
ENVIRONMENT=${ENVIRONMENT:-production}
PORT=${PORT:-8000}

echo "Starting EcoBot..."
echo "Environment: $ENVIRONMENT"
echo "Port: $PORT"

# Start application based on environment
if [ "$ENVIRONMENT" = "production" ]; then
    echo "Starting in production mode..."
    exec python3 main.py --production
else
    echo "Starting in development mode..."
    exec python3 main.py
fi
