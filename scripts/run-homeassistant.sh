#!/usr/bin/env bash
# Run Home Assistant for testing the Solar Window System custom component

set -e

cd "$(dirname "$0")/.."

# Handle --clean parameter
if [ "$1" == "--clean" ]; then
  echo "Cleaning .storage directory..."
  rm -rf "${PWD}/config/.storage"
  echo "Cleaning HomeAssistant DB..."
  rm -rf "${PWD}/config/home-assistant_v2.db"
  echo "Done"
fi

# Create config dir if not present
if [[ ! -d "${PWD}/config" ]]; then
    mkdir -p "${PWD}/config"
    hass --config "${PWD}/config" --script ensure_config
fi

# Remove __pycache__ directories
find ./custom_components -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true

# Set the path to custom_components
## This let's us have the structure we want <root>/custom_components/solar_window_system
## while at the same time have Home Assistant configuration inside <root>/config
## without resulting to symlinks.
export PYTHONPATH="${PYTHONPATH}:${PWD}/custom_components"

# Start Home Assistant
echo "Starting Home Assistant..."
hass --config "${PWD}/config" --debug
