#!/bin/bash

set -e

echo "========================================="
echo "  DevContainer Setup - Solar Window System"
echo "========================================="
echo ""

# Ensure config directory exists
mkdir -p /workspaces/solar_window_system/config

# Initialize Home Assistant config if not present
if [ ! -f /workspaces/solar_window_system/config/configuration.yaml ]; then
    echo "Initializing Home Assistant configuration..."
    python3 -m homeassistant --config /workspaces/solar_window_system/config --script ensure_config
fi

# Set proper permissions
chmod -R 755 /workspaces/solar_window_system/custom_components

# Install pre-commit hooks if .git exists
if [ -d /workspaces/solar_window_system/.git ]; then
    echo "Setting up git hooks..."
    cd /workspaces/solar_window_system
    cp .git-hooks/commit-msg .git/hooks/
    chmod +x .git/hooks/commit-msg
fi

echo ""
echo "========================================="
echo "  Setup complete!"
echo "  Run 'scripts/start-ha.sh' to start Home Assistant"
echo "========================================="
