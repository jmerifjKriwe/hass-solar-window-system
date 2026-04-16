# Quality Gate Guide

This guide explains how to use the quality gate for the Solar Window System project.

## Quick Start

### DevContainer Development (Recommended)

This project is designed for VS Code DevContainer. All tools are pre-installed.

Run quality checks:
```bash
./scripts/quality-gate.sh
```

This runs all quality checks:
- ✓ Ruff format (code formatting)
- ✓ Ruff lint (linting)
- ✓ Pyright (type checking)
- ✓ Pytest (all tests)

### Pre-commit Hooks

Quality gate is integrated into git pre-commit hooks and runs automatically on commit.

## Quality Gate Results

All checks passed:

```
=========================================
  Solar Window System - Quality Gate
=========================================

✓ PASSED: Ruff format (code formatting)
✓ PASSED: Ruff lint (linting)
✓ PASSED: Pyright (type checking)
✓ PASSED: Pytest (38 tests)

=========================================
  Quality Gate Summary
=========================================
✓ All checks passed!

Code is ready to commit.
```

## Development Environment

### DevContainer (Recommended)

The project uses VS Code DevContainer with all dependencies pre-installed:

**Setup:**
1. Open project in VS Code
2. Click "Reopen in Container" when prompted
3. Wait for container build (first time only)

**Daily workflow:**
```bash
# Make changes and test
./scripts/quality-gate.sh

# Commit
git commit -m "feat: your changes"
```

### Local Development (Advanced)

For local development without DevContainer, install dependencies from `requirements-test.txt` directly.

## Configuration

### pyproject.toml

The project uses `pyproject.toml` for tool configuration:

- **Ruff format**: Line length 100, Python 3.10+ support (replaces Black)
- **Ruff lint**: Fast linting with auto-fix
- **Pyright**: Type checking with HA import warnings suppressed (expected)
- **Pytest**: Async support, coverage reporting

### .pre-commit-config.yaml

Pre-commit hooks configuration:
- Ruff format: Code formatting
- Ruff lint: Linting with auto-fix
- Quality Gate: Runs all checks before commit

## Troubleshooting

### Permission Denied on Scripts

```bash
chmod +x scripts/*.sh
```

### Pyright Shows Import Errors

**Problem**: "Import 'homeassistant' could not be resolved"
**Solution**: These are expected! HA is not installed in dev environment. The `pyproject.toml` is configured to ignore these errors.

### Quality Gate Fails

**Problem**: Ruff formatting or linting issues
**Solution**: Run auto-fix:
```bash
ruff format .
ruff check --fix .
```


## Daily Workflow

### 1. Make Changes

```bash
# Edit code
vim custom_components/solar_window_system/coordinator.py
```

### 2. Run Tests

```bash
# Quick test
pytest tests/test_coordinator.py -v

# Full test suite
pytest tests/
```

### 3. Check Quality

```bash
./scripts/quality-gate.sh
```

### 4. Fix Issues (if any)

```bash
# Auto-fix formatting and linting
ruff format .
ruff check --fix .

# Run quality gate again
./scripts/quality-gate.sh
```

### 5. Commit

```bash
git add .
git commit -m "feat: your changes"
# Pre-commit hooks run automatically
```

## Quality Check Details

### Ruff Format (Code Formatting)

- Line length: 100 characters
- Target Python: 3.14
- Single tool for format + lint
- Excludes: build artifacts, cache directories

### Ruff Lint (Linting)

- Fast Python linter
- Auto-fixes import ordering and common issues
- Ignores F401 (unused imports for type hints)

### Pyright (Type Checking)

- Static type checking
- HA import warnings suppressed (expected in dev environment)

### Pytest (Testing)

- All tests passing
- Test coverage: coordinator, sensor, store, constants
- Async support enabled
- Coverage reporting available

## Project Status

✅ **All quality checks passing**
- Code formatted with Ruff
- No linting errors (Ruff)
- No type errors (Pyright)
- All tests passing (38/38)
- Home Assistant 2026.2.3 compatible

The project is ready for development and contributions.

## Additional Resources

- **scripts/README.md**: Complete script documentation
- **CLAUDE.md**: Project overview and architecture
- **pyproject.toml**: Tool configuration
- **pytest.ini**: Test configuration

---

**Last Updated**: 2026-03-04
**Status**: All quality checks passing ✓
**Tools**: Ruff 0.9.9 (format + lint), Pyright, Pytest
**Home Assistant**: 2026.2.3
