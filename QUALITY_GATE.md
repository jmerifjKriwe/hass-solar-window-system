# Quality Gate Guide

This guide explains how to use the quality gate and development environment setup for the Solar Window System project.

## Quick Start

### Option 1: Manual Quality Check (Recommended)

Run the quality gate manually before committing:

**Windows (PowerShell/cmd):**
```powershell
scripts\quality-gate.bat
```

**Linux/Mac/Git Bash:**
```bash
./scripts/quality-gate.sh
```

This will run all quality checks:
- ✓ Ruff format (code formatting)
- ✓ Ruff lint (linting)
- ✓ Pyright (type checking)
- ✓ Pytest (38 tests)

### Option 2: Automatic Pre-commit Hooks

The quality gate is integrated into git pre-commit hooks. However, on Windows you may encounter Python version issues. If pre-commit hooks don't work, use Option 1.

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

## Development Environments

### Dev Environment (`venv/`)

For daily development with quality tools:

**Windows:**
```powershell
# Set up dev environment (first time only)
scripts\setup-dev.bat

# Activate dev environment
venv\Scripts\activate

# Make changes and test
scripts\quality-gate.bat

# Commit when quality gate passes
git commit -m "your changes"
```

**Linux/Mac:**
```bash
# Set up dev environment (first time only)
./scripts/setup-dev.sh

# Activate dev environment
source venv/bin/activate

# Make changes and test
./scripts/quality-gate.sh

# Commit when quality gate passes
git commit -m "your changes"
```

### Home Assistant Test Environment (`ha_test_env/`)

For testing with real Home Assistant code:

**Windows:**
```powershell
# Set up HA test environment (first time only)
scripts\setup-homeassistant-test.bat

# Activate test environment
activate_test_env.bat

# Run tests
python test_runner.py

# Deactivate when done
deactivate
```

**Linux/Mac:**
```bash
# Set up HA test environment (first time only)
./scripts/setup-homeassistant-test.sh

# Activate test environment
source activate_test_env.sh

# Run tests
python test_runner.py

# Deactivate when done
deactivate
```

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

### Windows: How to Run Scripts

**Problem**: Don't know how to run .sh scripts on Windows
**Solution**: Use the provided .bat files:
```powershell
# Quality gate
scripts\quality-gate.bat

# Setup dev environment
scripts\setup-dev.bat

# Setup HA test environment
scripts\setup-homeassistant-test.bat
```

### Pre-commit Hooks Fail on Windows

**Problem**: Pre-commit can't find Python 3.12
**Solution**: Use manual quality gate: `scripts\quality-gate.bat` (Windows) or `./scripts/quality-gate.sh` (Linux/Mac)

### Pyright Shows Import Errors

**Problem**: "Import 'homeassistant' could not be resolved"
**Solution**: These are expected! HA is not installed in dev environment. The `pyproject.toml` is configured to ignore these errors.

### Tests Pass but Quality Gate Fails

**Problem**: Ruff formatting or linting issues
**Solution**: Run auto-fix:
```bash
ruff format .
ruff check --fix .
```

### HA Test Environment Issues

**Problem**: Tests fail in HA environment
**Solution**: Make sure you activated the right environment:
```bash
source activate_test_env.sh  # Not venv!
python test_runner.py
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

**Windows:**
```powershell
# Run all quality checks
scripts\quality-gate.bat
```

**Linux/Mac:**
```bash
# Run all quality checks
./scripts/quality-gate.sh
```

### 4. Fix Issues (if any)

```powershell
# Auto-fix formatting and linting
ruff format .
ruff check --fix .

# Run quality gate again
scripts\quality-gate.bat
```

### 5. Commit

```bash
git add .
git commit -m "feat: your changes"
# Pre-commit hooks run automatically (if configured)
```

## Quality Check Details

### Ruff Format (Code Formatting)

- Line length: 100 characters
- Target Python: 3.10, 3.11, 3.12, 3.13
- Replaces Black (single tool for format + lint)
- Excludes: venv, ha_test_env, build artifacts

### Ruff Lint (Linting)

- Fast Python linter
- Auto-fixes import ordering and common issues
- Ignores F401 (unused imports for type hints)

### Pyright (Type Checking)

- Static type checking
- 0 errors, 0 warnings, 0 informations
- HA import warnings suppressed (expected)

### Pytest (Testing)

- 38 tests, all passing
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
