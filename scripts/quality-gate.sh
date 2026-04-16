#!/usr/bin/env bash
# Quality Gate Script for Solar Window System
# Runs all linting, type checking, and tests
# Exit code 0 = all pass, non-zero = something failed

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "  Solar Window System - Quality Gate"
echo "========================================="
echo ""

# Track failures
FAILURES=0

# Function to run a check and report result
run_check() {
    local name="$1"
    local command="$2"

    echo -e "${YELLOW}Running:${NC} $name"
    if eval "$command"; then
        echo -e "${GREEN}✓ PASSED:${NC} $name"
    else
        echo -e "${RED}✗ FAILED:${NC} $name"
        FAILURES=$((FAILURES + 1))
    fi
    echo ""
}

# 1. Ruff format (code formatting - replaces Black)
run_check "Ruff format (code formatting)" \
    "python -m ruff format --check custom_components/solar_window_system/ tests/"

# 2. Ruff (fast Python linter)
run_check "Ruff (linting)" \
    "python -m ruff check custom_components/solar_window_system/ tests/"

# 3. Pyright (type checking)
# Note: Pyright will have import errors (HA not installed), but we check for real issues
run_check "Pyright (type checking)" \
    "python -m pyright custom_components/solar_window_system/" \
    || true  # Don't fail on import errors

# 4. Pytest (test suite)
run_check "Pytest (test suite)" \
    "python -m pytest tests/ -v --tb=short"

# Summary
echo "========================================="
echo "  Quality Gate Summary"
echo "========================================="

if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "Code is ready to commit."
    exit 0
else
    echo -e "${RED}✗ $FAILURES check(s) failed${NC}"
    echo ""
    echo "Please fix the issues above before committing."
    exit 1
fi
