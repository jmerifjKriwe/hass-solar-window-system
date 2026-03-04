# Development Scripts

This directory contains scripts for development and testing of the Solar Window System Home Assistant integration.

## Scripts

### Quality Gate

**File:** `quality-gate.sh`

Runs all quality checks before committing:
- Black (code formatting)
- Ruff (linting)
- Pyright (type checking)
- Pytest (test suite)

**Usage:**
```bash
./scripts/quality-gate.sh
```

**Exit codes:**
- `0` - All checks passed
- `1` - One or more checks failed

**Integration:** Automatically run by pre-commit hooks.

---

### Development Environment Setup

**File:** `setup-dev.sh`

Sets up a complete Python development environment for working on the custom component.

**What it does:**
1. Checks Python version (requires 3.10+)
2. Creates virtual environment (`venv/`)
3. Installs all development dependencies:
   - pytest and plugins
   - black, ruff, pyright
   - pre-commit
   - type stubs
4. Installs pre-commit hooks
5. Runs initial quality gate

**Usage:**
```bash
./scripts/setup-dev.sh
```

**After setup:**
```bash
source venv/bin/activate  # Activate dev environment
pytest tests/              # Run tests
black .                    # Format code
./scripts/quality-gate.sh # Run all checks
```

---

### Home Assistant Test Environment

**File:** `setup-homeassistant-test.sh`

Creates an isolated test environment with Home Assistant installed.

**Why use this?**
- Tests your component with real HA code
- Isolated from your dev environment
- No conflicts with your system's HA installation
- Easy to recreate if something breaks

**What it does:**
1. Creates `ha_test_env/` virtual environment
2. Installs Home Assistant 2024.3.0
3. Installs test dependencies
4. Creates test runner script
5. Creates activation scripts

**Usage:**
```bash
./scripts/setup-homeassistant-test.sh
source activate_test_env.sh
python test_runner.py
```

**Test environment features:**
- Full Home Assistant integration
- Real HA entities and services
- Proper testing of all integration points

---

## Quick Reference

### Setup for First Time

```bash
# 1. Set up dev environment
./scripts/setup-dev.sh

# 2. Activate dev environment
source venv/bin/activate

# 3. Install pre-commit hooks (already done by setup-dev.sh)
pre-commit install
```

### Daily Development Workflow

```bash
# Activate dev environment
source venv/bin/activate

# Make some changes...
git add .
git commit -m "feat: my changes"
# Pre-commit hooks run automatically
```

### Run Tests Manually

```bash
# In dev environment
pytest tests/ -v

# In HA test environment (for integration tests)
source activate_test_env.sh
python test_runner.py
```

### Quality Checks

```bash
# Run all checks
./scripts/quality-gate.sh

# Run individually
black --check .
ruff check .
python -m pytest tests/
```

---

## Script Details

### quality-gate.sh

**Purpose:** Automated quality checking before commits.

**Checks performed:**
1. **Black** - Code formatting
2. **Ruff** - Fast Python linter
3. **Pyright** - Static type checking
4. **Pytest** - Test suite (38 tests)

**Exit codes:**
- `0` - All passed
- `1` - One or more failed

**Note:** Pyright import errors are expected (HA not installed in dev env) and don't cause failure.

---

### setup-dev.sh

**Purpose:** Create complete development environment.

**Installs:**
```
Testing:
- pytest (test framework)
- pytest-asyncio (async test support)
- pytest-homeassistant-custom-component (HA testing)
- pytest-cov (coverage)
- pytest-timeout (timeout handling)
- pytest-xdist (parallel tests)

Code Quality:
- black (code formatter)
- ruff (fast linter)
- pyright (type checker)

Development:
- pre-commit (git hooks)
- types-homeassistant-stubs (type hints)
```

**Requirements:**
- Python 3.10 or higher
- pip
- Virtual environment support

**Output:**
- `venv/` - Virtual environment
- `requirements-dev.txt` - Pinned dependencies
- Pre-commit hooks installed

---

### setup-homeassistant-test.sh

**Purpose:** Create isolated HA test environment.

**Why separate environment?**
- HA has many dependencies
- Dev env focuses on tools, test env on HA
- Easy to recreate if broken
- No conflicts with system HA

**Creates:**
```
ha_test_env/
├── bin/activate
├── lib/python3.XX/site-packages/
│   ├── homeassistant/
│   └── pytest_homeassistant_custom_component/
└── ...
```

**Usage:**
```bash
# Set up environment
./scripts/setup-homeassistant-test.sh

# Activate and test
source activate_test_env.sh
python test_runner.py

# Deactivate when done
deactivate
```

---

## Troubleshooting

### Script Permission Denied

```bash
chmod +x scripts/*.sh
```

### Python Version Too Old

```bash
# Check version
python --version

# You need Python 3.10+
# Install from python.org
```

### Virtual Environment Activation Issues

**Windows:**
```bash
# If activate.bat doesn't work
ha_test_env\Scripts\activate
```

**Linux/Mac:**
```bash
# If activate.sh doesn't work
source ha_test_env/bin/activate
```

### Pre-commit Hooks Not Running

```bash
# Install hooks
pre-commit install

# Verify
pre-commit run --all-files
```

### Tests Fail in HA Environment

```bash
# Make sure you're in the right directory
pwd  # Should show solar_window_system

# Activate test environment first
source activate_test_env.sh

# Run tests
python test_runner.py
```

---

## Advanced Usage

### Parallel Testing with pytest-xdist

```bash
pytest -n auto  # Auto-detect CPU count
```

### Coverage Report

```bash
pytest --cov=custom_components/solar_window_system --cov-report=html
# Open htmlcov/index.html
```

### Watch Mode (auto-run on changes)

```bash
pytest-watch tests/
```

### Verbose Output

```bash
pytest -vv tests/test_coordinator.py::test_sun_is_visible
```

---

## Integration with CI/CD

These scripts are already integrated into GitHub Actions:

- **`.github/workflows/ci.yaml`** - Runs quality gate on every push/PR
- **`.github/workflows/validate.yaml`** - Validates HA integration

**Local testing mimics CI:**
```bash
./scripts/quality-gate.sh  # Same as CI workflow
```

---

## Maintenance

### Updating Dependencies

```bash
# Activate dev environment
source venv/bin/activate

# Update all
pip install --upgrade -r requirements-dev.txt

# Run tests
pytest tests/
```

### Updating Pre-commit Hooks

```bash
pre-commit autoupdate
pre-commit install
```

### Clean Restart

```bash
# Remove everything and start fresh
rm -rf venv ha_test_env
./scripts/setup-dev.sh
./scripts/setup-homeassistant-test.sh
```

---

## Additional Resources

- **pytest documentation:** https://docs.pytest.org/
- **Home Assistant testing:** https://developers.home-assistant.io/docs/testing/testing_integration/
- **pre-commit documentation:** https://pre-commit.com/
- **Black formatter:** https://black.readthedocs.io/
- **Ruff linter:** https://docs.astral.sh/ruff/
