#!/bin/sh
set -e

# Replace environment variables in index.html
sed -i "s|\${BACKEND_URL}|${BACKEND_URL}|g" /app/index.html

# Start the HTTP server
exec "$@"