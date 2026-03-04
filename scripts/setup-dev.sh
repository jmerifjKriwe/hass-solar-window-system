#!/usr/bin/env bash
# Development Environment Setup for Solar Window System
# Sets up a complete Python environment for HA custom component development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================="
echo "  Solar Window System - Dev Setup"
echo "========================================="
echo ""

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

echo -e "${BLUE}Python version:${NC} $PYTHON_VERSION"

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo -e "${RED}Error:${NC} Python 3.10+ required"
    exit 1
fi

echo -e "${GREEN}✓ Python version OK${NC}"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
fi
echo ""

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate || source venv/Scripts/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel > /dev/null
echo -e "${GREEN}✓ pip upgraded${NC}"
echo ""

# Install core dependencies
echo -e "${YELLOW}Installing core dependencies...${NC}"

# Testing framework
pip install pytest==8.0.0 \
    pytest-asyncio==0.23.4 \
    pytest-homeassistant-custom-component==0.13.104 \
    pytest-cov==4.1.0 \
    pytest-timeout==2.3.1 \
    pytest-xdist==3.5.0 \
    > /dev/null
echo -e "${GREEN}  ✓ pytest (testing framework)${NC}"

# Code quality tools
pip install \
    ruff==0.15.4 \
    pyright==1.1.408 \
    > /dev/null
echo -e "${GREEN}  ✓ ruff (format + lint), pyright (type checking)${NC}"

# Type stubs (optional, for better IDE support)
pip install types-homeassistant-stubs==2026.2.3 \
    > /dev/null 2>&1 || echo -e "${YELLOW}  ! types-homeassistant-stubs not available (optional)${NC}"
echo -e "${GREEN}  ✓ type stubs (optional)${NC}"

echo ""
echo -e "${GREEN}✓ Core dependencies installed${NC}"
echo ""

# Create requirements.txt for reproducibility
echo -e "${YELLOW}Creating requirements.txt...${NC}"
cat > requirements-dev.txt << 'EOF'
# Core testing framework
pytest==8.0.0
pytest-asyncio==0.23.4
pytest-homeassistant-custom-component==0.13.104
pytest-cov==4.1.0
pytest-timeout==2.3.1
pytest-xdist==3.5.0

# Code quality
ruff==0.15.4
pyright==1.1.408

# Type stubs (optional)
types-homeassistant-stubs==2026.2.3

# Development tools
pre-commit==3.7.0
EOF
echo -e "${GREEN}✓ requirements-dev.txt created${NC}"
echo ""

# Install pre-commit hooks
echo -e "${YELLOW}Installing pre-commit hooks...${NC}"
pip install pre-commit > /dev/null
pre-commit install > /dev/null
echo -e "${GREEN}✓ pre-commit hooks installed${NC}"
echo ""

# Install git commit-msg hook
echo -e "${YELLOW}Installing git commit-msg hook...${NC}"
./scripts/install-hooks.sh
echo ""

# Run initial quality gate
echo -e "${YELLOW}Running initial quality gate...${NC}"
echo ""
./scripts/quality-gate.sh

echo ""
echo "========================================="
echo "  Development Environment Ready!"
echo "========================================="
echo ""
echo -e "${BLUE}To activate the environment, run:${NC}"
echo "  source venv/bin/activate  # Linux/Mac"
echo "  venv\\Scripts\\activate   # Windows"
echo ""
echo -e "${BLUE}To deactivate, run:${NC}"
echo "  deactivate"
echo ""
echo -e "${BLUE}To run tests:${NC}"
echo "  pytest tests/"
echo ""
echo -e "${BLUE}To run quality gate:${NC}"
echo "  ./scripts/quality-gate.sh"
echo ""
echo -e "${BLUE}To format code:${NC}"
echo "  ruff format ."
echo ""
echo -e "${BLUE}For Home Assistant testing:${NC}"
echo "  See scripts/setup-homeassistant-test.sh"
echo ""
