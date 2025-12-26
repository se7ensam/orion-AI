#!/bin/bash
# Helper script to run the Orion Downloader

# Ensure we're in the right directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if dist exists
if [ ! -d "dist" ]; then
    echo "Building downloader..."
    npm install
    npm run build
fi

# Run the downloader
echo "Running Orion Downloader..."
echo "Args: $@"
node dist/index.js "$@"
