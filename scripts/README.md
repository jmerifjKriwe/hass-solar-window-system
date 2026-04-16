# Development Scripts

This directory contains scripts for development and testing of the Solar Window System Home Assistant integration.

## DevContainer Development (Recommended)

This project is designed for **VS Code DevContainer**:
- See `.devcontainer/README.md` for setup
- All dependencies pre-installed in container
- No local Python/venv setup required

## Scripts

### Quality Gate

**File:** `quality-gate.sh`

Runs all quality checks before committing:
- Ruff format (code formatting)
- Ruff lint (linting)
- Pyright (type checking)
- Pytest (test suite)

**Usage:**
```bash
./scripts/quality-gate.sh
```

**Exit codes:**
- `0` - All checks passed
- `1` - One or more checks failed

---

## Quick Reference

### Setup for First Time

**DevContainer:**
```bash
# Open in DevContainer (VS Code will prompt)
# Dependencies are pre-installed
```

### Daily Development Workflow

```bash
# Make some changes...
git add .
git commit -m "feat: my changes"
# Pre-commit hooks run automatically
```

### Run Tests Manually

```bash
pytest tests/ -v
```

### Quality Checks

```bash
# Run all checks
./scripts/quality-gate.sh

# Run individually
ruff format --check .
ruff check .
python -m pytest tests/
```

---

## Script Details

### quality-gate.sh

**Purpose:** Automated quality checking before commits.

**Checks performed:**
1. **Ruff format** - Code formatting
2. **Ruff lint** - Fast Python linter
3. **Pyright** - Static type checking
4. **Pytest** - Test suite

**Exit codes:**
- `0` - All passed
- `1` - One or more failed

**Note:** Pyright import errors are expected (HA not installed in dev env) and don't cause failure.

---

## Troubleshooting

### Script Permission Denied

```bash
chmod +x scripts/*.sh
```

### Pre-commit Hooks Not Running

```bash
# Install hooks
pre-commit install

# Verify
pre-commit run --all-files
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

### Verbose Output

```bash
pytest -vv tests/test_coordinator.py::test_sun_is_visible
```

---

## Integration with CI/CD

These scripts are integrated into GitHub Actions:

- **`.github/workflows/ci.yaml`** - Runs quality gate on every push/PR
- **`.github/workflows/validate.yaml`** - Validates HA integration

**Local testing mimics CI:**
```bash
./scripts/quality-gate.sh  # Same as CI workflow
```

---

## Maintenance

### Updating Dependencies

Dependencies are managed via `requirements-test.txt` and installed in the DevContainer.

### Updating Pre-commit Hooks

```bash
pre-commit autoupdate
pre-commit install
```

---

## Additional Resources

- **pytest documentation:** https://docs.pytest.org/
- **Home Assistant testing:** https://developers.home-assistant.io/docs/testing/testing_integration/
- **pre-commit documentation:** https://pre-commit.com/
- **Black formatter:** https://black.readthedocs.io/
- **Ruff linter:** https://docs.astral.sh/ruff/
