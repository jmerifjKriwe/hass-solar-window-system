#!/usr/bin/env bash
# Install git hooks from .git-hooks directory

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "Installing git hooks..."

# Create .git/hooks directory if it doesn't exist
mkdir -p .git/hooks

# Copy hooks
cp .git-hooks/commit-msg .git/hooks/commit-msg

# Make executable
chmod +x .git/hooks/commit-msg

echo -e "${GREEN}✓ Git hooks installed${NC}"
echo ""
echo "Installed hooks:"
echo "  - commit-msg: Validates Conventional Commits format"
echo ""
echo "See COMMIT_CONVENTIONS.md for details."
