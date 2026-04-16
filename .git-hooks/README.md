# Git Hooks

This directory contains git hooks for the Solar Window System project.

## Available Hooks

### commit-msg

Validates that commit messages follow the Conventional Commits format.

**Format:** `type(scope): description`

**Valid types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Code style
- `refactor` - Code refactoring
- `perf` - Performance
- `test` - Tests
- `chore` - Maintenance
- `ci` - CI/CD
- `build` - Build system/dependencies
- `revert` - Revert commit

## Installation

### Automatic (Recommended)

The hooks are installed automatically in the DevContainer via `.devcontainer/post-create.sh`.

### Manual Installation

```bash
# Copy hooks to .git/hooks
./scripts/install-hooks.sh
```

## Testing

To test the commit-msg hook:

```bash
# This should succeed
git commit -m "feat(coordinator): add diffuse radiation estimation"

# This should fail
git commit -m "update stuff"
```

## For AI Agents

When creating commits, follow this format:

```
type(scope): description

Detailed explanation of what was changed and why.

Footer for breaking changes or references.
```

See `COMMIT_CONVENTIONS.md` for complete documentation.
