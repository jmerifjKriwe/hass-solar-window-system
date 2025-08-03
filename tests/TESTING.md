# Solar Window System Integration Testing Guide

This document describes the testing strategy and implementation for the Home Assistant integration `solar_window_system`.

## Table of Contents
1. [Test Structure and Organization](#test-structure-and-organization)
2. [Testing Conventions](#testing-conventions)
3. [Test Execution](#test-execution)
4. [Test Types and Strategies](#test-types-and-strategies)
5. [Error Handling](#error-handling)
6. [Fixtures and Test Data](#fixtures-and-test-data)
7. [Best Practices](#best-practices)

---

## Test Structure and Organization

The tests for the `solar_window_system` integration are structured as follows:

| File | Description |
|-------|-------------|
| `test_config_flow_global.py` | Tests for the global configuration flow (initial setup) |
| `test_config_flow_window.py` | Tests for the window configuration flow (initial setup) |
| `test_options_flow_global.py` | Tests for the global options flow (subsequent adjustments) |
| `test_options_flow_window.py` | Tests for the window options flow (subsequent adjustments) |
| `conftest.py` | Global fixtures and shared test data |
| `mocks.py` | Mock objects and helper functions for tests |

*Note: Tests for the group flow will be added in the future.*

---

## Testing Conventions

All tests use `pytest` and the `pytest-homeassistant-custom-component` plugin.

### General Structure

```python
@pytest.mark.asyncio
async def test_something_specific(hass, fixture1, fixture2):
    """A clear description of what this test verifies."""
    # Test setup
    # Perform actions
    # Assertions
```

### Naming Conventions

- Test functions start with `test_`
- Names should clearly describe what is being tested
- Use meaningful docstrings for each test

---

## Test Execution

### Running All Tests

```bash
# In the project root directory:
python -m pytest
```

### Running Specific Tests

```bash
# Only config flow tests:
python -m pytest tests/test_config_flow_*.py

# Only a specific test:
python -m pytest tests/test_config_flow_global.py::test_global_config_flow_valid_input

# With verbose output:
python -m pytest tests/test_config_flow_global.py -v
```

---

## Test Types and Strategies

### Config Flow Tests

Config flow tests verify the initial configuration of the integration or a window.

#### Initializing a Config Flow:

```python
# Start flow
result = await hass.config_entries.flow.async_init(
    DOMAIN, context={"source": "user"}
)

# Continue with user input
result = await hass.config_entries.flow.async_configure(
    result["flow_id"], user_input={"entry_type": "global"}
)
```

#### Validating the Flow Result:

```python
# Check current step
assert result["step_id"] == "global_init"

# Check result type
assert result["type"] == "form"  # or "create_entry" or "abort"

# On success (final step)
assert result["type"] == "create_entry"
```

### Options Flow Tests

Options flow tests verify subsequent changes to the configuration.

#### Initializing an Options Flow:

```python
# Start options flow
result = await hass.config_entries.options.async_init(entry.entry_id)

# Continue with user input
result = await hass.config_entries.options.async_configure(
    result["flow_id"], user_input=valid_input
)
```

---

## Error Handling

There are two different approaches to error handling in our tests:

### 1. Config Flow: Checking Errors in Result

In config flows, errors are typically returned in the result dictionary:

```python
# Send invalid input
result = await hass.config_entries.flow.async_configure(
    result["flow_id"],
    user_input={"update_interval": "invalid"},
)

# Check for errors
assert result["type"] == "form"
assert "errors" in result
assert "update_interval" in result["errors"]
```

### 2. Options Flow: Catching Schema Validation Errors with pytest.raises

In options flows, schema validation errors are thrown as exceptions:

```python
# Check for exception on invalid input
with pytest.raises(Exception) as excinfo:
    await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"g_value": 2.0},  # Invalid value
    )

# Check error message
assert "Schema validation failed" in str(excinfo.value)
```

---

## Fixtures and Test Data

Shared fixtures and test data are defined in `conftest.py`:

### Important Fixtures

- `valid_global_input`: Valid inputs for global configuration
- `valid_thresholds`: Valid threshold values for global configuration
- `valid_global_options`: Valid options for global configuration
- `valid_window_input`: Valid inputs for window configuration
- `valid_window_options`: Valid options for window configuration
- `window_entry`: Mock for a window config entry

### Example of Fixture Usage

```python
@pytest.mark.asyncio
async def test_with_fixtures(hass, valid_global_input):
    """Tests something with the predefined fixtures."""
    # Test implementation using valid_global_input
```

---

## Best Practices

### 1. Always Test Both Paths

- Positive tests (valid inputs)
- Negative tests (invalid inputs, missing required fields)

### 2. Test Boundary Conditions

- Minimum and maximum values
- Edge cases such as empty lists or strings

### 3. Use Assertions Correctly

- Use specific assertions
- Provide detailed error messages for complex conditions

### 4. Keep Tests Independent

- No dependencies between tests
- Each test should set up its own environment

### 5. Follow DRY Principle in Tests

- Extract common code into helper functions or fixtures
- Use fixtures for recurring setups

---

## Future Enhancements

- Tests for group configuration and options
- More parameterization for broader test coverage
- Integration tests for interaction between multiple components
- Performance tests for computationally intensive operations
