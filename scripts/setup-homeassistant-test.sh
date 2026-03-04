#!/usr/bin/env bash
# Home Assistant Test Environment Setup
# Sets up a test environment for testing the custom component

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "========================================="
echo "  Home Assistant Test Environment Setup"
echo "========================================="
echo ""

echo -e "${YELLOW}This script will:${NC}"
echo "1. Install Home Assistant in a Python virtual environment"
echo "2. Set up necessary test dependencies"
echo "3. Create a test configuration"
echo ""
echo -e "${YELLOW}Note:${NC} This creates a TEST environment, not for production use!"
echo ""

# Create HA-specific virtual environment
HA_VENV="ha_test_env"

if [ -d "$HA_VENV" ]; then
    echo -e "${YELLOW}Removing old test environment...${NC}"
    rm -rf "$HA_VENV"
fi

echo -e "${YELLOW}Creating Home Assistant test environment...${NC}"
python -m venv "$HA_VENV"
source "$HA_VENV/bin/activate" || source "$HA_VENV/Scripts/activate"

echo -e "${GREEN}✓ Test environment created${NC}"
echo ""

# Install Home Assistant with test dependencies
echo -e "${YELLOW}Installing Home Assistant (test version)...${NC}"
pip install \
    homeassistant==2024.3.0 \
    pytest-homeassistant-custom-component==0.13.104 \
    > /dev/null

echo -e "${GREEN}✓ Home Assistant installed${NC}"
echo ""

# Create test configuration script
echo -e "${YELLOW}Creating test runner...${NC}"
cat > test_runner.py << 'EOF'
#!/usr/bin/env python3
"""Test runner for Solar Window System in isolated HA environment."""

import os
import sys
import subprocess

def run_tests():
    """Run tests in the HA environment."""
    print("=" * 50)
    print("  Solar Window System - Test Runner")
    print("=" * 50)
    print()
    print("Running tests with Home Assistant integration...")
    print()

    # Run pytest
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            "tests/",
            "-v",
            "--tb=short",
            "--cov=custom_components/solar_window_system",
            "--cov-report=term-missing"
        ],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )

    return result.returncode

if __name__ == "__main__":
    sys.exit(run_tests())
EOF

chmod +x test_runner.py

echo -e "${GREEN}✓ Test runner created${NC}"
echo ""

# Create activation script
echo -e "${YELLOW}Creating activation scripts...${NC}"

# Linux/Mac activation
cat > activate_test_env.sh << 'EOF'
#!/bin/bash
# Activate the Home Assistant test environment

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$SCRIPT_DIR/ha_test_env/bin/activate"

echo "Home Assistant test environment activated"
echo "Python: $(python --version)"
echo "Home Assistant: $(python -c 'import homeassistant; print(homeassistant.__version__)')"
echo ""
echo "To run tests:"
echo "  python test_runner.py"
echo ""
echo "To deactivate:"
echo "  deactivate"
EOF

chmod +x activate_test_env.sh

# Windows activation
cat > activate_test_env.bat << 'EOF'
@echo off
REM Activate the Home Assistant test environment

call ha_test_env\Scripts\activate.bat

echo Home Assistant test environment activated
echo Python:
python --version
echo.
echo Home Assistant:
python -c "import homeassistant; print(homeassistant.__version__)"
echo.
echo To run tests:
echo   python test_runner.py
echo.
echo To deactivate:
echo   deactivate
EOF

echo -e "${GREEN}✓ Activation scripts created${NC}"
echo ""

# Create requirements file
cat > requirements-ha-test.txt << 'EOF'
# Home Assistant Test Environment
# Install with: pip install -r requirements-ha-test.txt

# Home Assistant core
homeassistant==2024.3.0

# Testing framework
pytest-homeassistant-custom-component==0.13.104

# Coverage reporting
pytest-cov==4.1.0
EOF

echo -e "${GREEN}✓ requirements-ha-test.txt created${NC}"
echo ""

echo "========================================="
echo "  Test Environment Setup Complete!"
echo "========================================="
echo ""
echo -e "${BLUE}To use the test environment:${NC}"
echo ""
echo "1. Activate the environment:"
echo "   source activate_test_env.sh   # Linux/Mac"
echo "   activate_test_env.bat       # Windows"
echo ""
echo "2. Run tests:"
echo "   python test_runner.py"
echo ""
echo "3. Deactivate when done:"
echo "   deactivate"
echo ""
echo -e "${YELLOW}Note:${NC} This environment is isolated from your dev environment."
echo "You can switch between dev (venv) and test (ha_test_env) as needed."
