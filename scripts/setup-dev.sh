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

# Check Python 3.14
echo -e "${BLUE}Checking Python version...${NC}"

if command -v python3.14 &>/dev/null; then
    PYTHON_CMD="python3.14"
elif command -v py &>/dev/null && py -3.14 --version &>/dev/null 2>&1; then
    PYTHON_CMD="py -3.14"
else
    echo -e "${RED}Error:${NC} Python 3.14 not found"
    echo "Please install Python 3.14 from https://www.python.org/"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python version: $PYTHON_VERSION${NC}"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
    echo -e "${BLUE}  If you encounter issues, delete the venv folder and re-run this script${NC}"
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
echo -e "${YELLOW}Installing dependencies from requirements-test.txt...${NC}"
pip install -r requirements-test.txt > /dev/null
echo -e "${GREEN}  ✓ Dependencies installed${NC}"

echo ""
echo -e "${GREEN}✓ Core dependencies installed${NC}"
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