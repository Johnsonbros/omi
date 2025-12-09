#!/bin/bash
set -e

echo "Building Zeke Core..."

cd zeke-core

echo "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install --no-cache-dir -r requirements.txt
fi

echo "Building dashboard..."
cd dashboard
npm ci
npm run build

echo "Cleaning up dev dependencies..."
npm prune --production 2>/dev/null || true

echo "Build complete!"
