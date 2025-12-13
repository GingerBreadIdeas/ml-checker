#!/bin/sh
set -e

echo "Backend host: $VITE_BACKEND_HOST"
echo "API path: $VITE_API_PATH"

# Install any new dependencies if package.json has changed
if [ -f "/app/package.json" ]; then
    echo "Checking for new dependencies..."
    npm install
fi

# Execute the command passed to docker run
echo "Starting frontend with command: $@"
exec "$@"