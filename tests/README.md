````markdown
### Subentry Flow Test Pattern (2025-08) - CORRECTED

**Important:** For Group and Window subentry flows, the correct multi-step wizard pattern is:

#### Group Flow (2 steps):
1. **Step 1:** Call `async_step_user(group_data)` → expect `{"type": "form", "step_id": "enhanced"}`
2. **Step 2:** Call `async_step_enhanced(scenario_data)` → expect `{"type": "create_entry"}`

#### Window Flow (3 steps):
1. **Step 1:** Call `async_step_user(window_data)` → expect `{"type": "form", "step_id": "overrides"}`
2. **Step 2:** Call `async_step_overrides(enhanced_data)` → expect `{"type": "form", "step_id": "scenarios"}`
3. **Step 3:** Call `async_step_scenarios(scenario_data)` → expect `{"type": "create_entry"}`

#### Reconfigure Pattern:
- For reconfigure flows, start with `async_step_reconfigure(None)` then follow the same step pattern
- **Group reconfigure:** `async_step_reconfigure(None)` → `async_step_user(data)` → `async_step_enhanced(data)` → `{"type": "update_entry"}`
- **Window reconfigure:** `async_step_reconfigure(None)` → `async_step_user(data)` → `async_step_overrides(data)` → `async_step_scenarios(data)` → `{"type": "update_entry"}`

**Example (Group):**
```python
# Creation flow
result = await handler.async_step_user(group_data)
assert result["type"] == "form" and result["step_id"] == "enhanced"
result = await handler.async_step_enhanced(scenario_data)
assert result["type"] == "create_entry"

# Reconfigure flow
result = await handler.async_step_reconfigure(None)
assert result["type"] == "form" and result["step_id"] == "user"
result = await handler.async_step_user(group_data)
assert result["type"] == "form" and result["step_id"] == "enhanced"
result = await handler.async_step_enhanced(scenario_data)
assert result["type"] == "update_entry"
```

**CRITICAL:** Never call `async_step_user` repeatedly for all steps. Each step has its own method.

### String Conversion Fix for Voluptuous Schemas (2025-08)

**Issue:** Home Assistant config flows with voluptuous schemas fail with "expected str" errors when numeric defaults are used with string validation.

**Root Cause:** When a form field has a numeric default (e.g., `default=123`) but string validation (`str`), voluptuous raises "expected str" when the default value is used (field missing from input).

**Solution:** All `_ui_default` helper functions must convert values to strings:
```python
def _ui_default(key: str) -> str:
    value = stored_data.get(key, "")
    # CRITICAL: Always convert to string for voluptuous compatibility
    return str(value) if value not in ("", None) else ""
```

**Test Strategy:** Tests should verify that schema validation works with string conversions without "expected str" errors, particularly in reconfigure flows where stored numeric data is displayed in forms.
### Options Flow Storage Format (2025-08)

- The options flow for the global config entry stores **all values as strings** in the config entry options dict, regardless of whether the schema field is numeric or not.
- Tests for the options flow must always expect string values when reading from `entry.options`, even for fields like `window_width`, `g_value`, etc.
- This is required for compatibility with Home Assistant's config entry storage and is not a bug.
- Example: If you submit `window_width: "1.5"` in the options flow, the stored value will be the string `"1.5"`, not the float `1.5`.
## Special Notes: Config Flow & SubEntry Flow Testing (2025-08)

### Critical Architecture Understanding

- **Main ConfigFlow vs SubentryFlow Distinction:**
  - The main `SolarWindowSystemConfigFlow` only creates global config and parent entries
  - **Groups and Windows use SubentryFlows, NOT the main ConfigFlow**
  - `GroupSubentryFlowHandler` handles group creation/modification
  - `WindowSubentryFlowHandler` handles window creation/modification
  - Never use the main config flow to test group/window creation


### SubEntry Flow Testing Strategy

- **Reconfigure/Second Save Scenarios:**
  - To test reconfigure (second save) scenarios for group or window subentries, always use the handler's public `async_step_reconfigure` method.
  - Do not set private or unknown attributes (such as `_reconfigure_mode`, `subentry`, or `source`) directly on the handler.
  - Example:
    ```python
    # First save (creation)
    result = await flow_handler.async_step_user(user_input)
    # Second save (reconfigure)
    result2 = await flow_handler.async_step_reconfigure(user_input)
    ```
  - This ensures your test matches the actual Home Assistant flow logic and remains compatible with future updates.

- **Group/Window Configuration Testing:**
  - Use `GroupSubentryFlowHandler`/`WindowSubentryFlowHandler` directly in tests
  - Do NOT test via `hass.config_entries.flow.async_init` with `parent_entry_id`
  - That API is for Home Assistant UI integration, not for testing
  - Create the flow handler instance and set required attributes manually:
    ```python
    flow_handler = GroupSubentryFlowHandler()
    flow_handler.hass = hass
    flow_handler.handler = DOMAIN
    flow_handler.parent_entry_id = parent_entry.entry_id
    ```

- **Mock Setup for SubEntry Tests:**
  - Use `MockConfigEntry` for parent entries and global config
  - Add entries to hass via `entry.add_to_hass(hass)`
  - Mock helper functions like `get_temperature_sensor_entities`
  - Test each step of the subentry flow individually

### Test Architecture Insights (August 2025)

- **Config Flow Abortion with 'already_configured':**
  - This is CORRECT behavior for the main config flow when integration exists
  - The main flow should only run once to create global config + parent entries
  - Individual groups/windows are created via their respective SubentryFlows

- **Inheritance Testing:**
  - Test inheritance by using "-1" values in SubentryFlow inputs
  - Verify that inheritance values are properly resolved from global config
  - Test both explicit values and inheritance scenarios



### Centralized Test Data (2025-08)

- All test data dictionaries for config flows (e.g., global, group, window input dicts) must be defined centrally in `tests/test_data.py`.
- Test modules must import and use these shared dictionaries instead of duplicating or redefining them locally.
- This ensures consistency, maintainability, and reduces errors when updating test scenarios or required fields.
- Example usage:
  ```python
  from tests.test_data import VALID_GLOBAL_BASIC, VALID_GLOBAL_ENHANCED
  data = {"entry_type": "global_config"}
  data.update(VALID_GLOBAL_BASIC)
  data.update(VALID_GLOBAL_ENHANCED)
  entry = MockConfigEntry(data=data, ...)
  ```

### Window & Group Config/Inheritance Testing (2025-08)

- **Window Config & Inheritance:**
  - All window configuration and inheritance tests must use the `WindowSubentryFlowHandler` (a ConfigSubentryFlow), not the OptionsFlow.
- **Group Config & Inheritance:**
  - All group configuration and inheritance tests must use the `GroupSubentryFlowHandler` (a ConfigSubentryFlow), not the OptionsFlow.
  - The legacy pattern of testing group/config inheritance via the options flow is no longer supported and will abort with `reason: not_supported`.
  - To test group/window inheritance, instantiate the appropriate subentry flow handler and drive it through its steps (`async_step_user`, `async_step_enhanced`, etc.), patching subentry/group/global data as needed.
  - Do not use OptionsFlow for window or group config/inheritance logic; this is reserved for other entity types if implemented.
  - See `test_group_flow.py`, `test_group_flow_fixed.py`, and `test_group_flow_defaults.py` for correct, modern test patterns.

#### Deprecated: Window Options Flow Testing

- As of August 2025, **window options flow is not supported**. Any attempt to test window configuration via the options flow will abort with `reason: not_supported`.
- The test `test_window_second_save_bug.py` was removed because it attempted to test window options flow, which is now architecturally unsupported. All window configuration/inheritance logic must be tested via the `WindowSubentryFlowHandler`.
- If you need to test window config/inheritance, use the subentry flow handler directly as described above.


#### Refactoring Note (2025-08)
- All legacy group flow tests using the options flow have been refactored to use the subentry flow handler directly. This is now the only supported and future-proof approach. If you see a test using the options flow for group/window config, it is outdated and must be refactored.

### Test Refactoring Workflow

- **Test Refactoring Workflow:**
  - Always refactor one test file at a time: refactor, ensure all tests are green, then proceed to the next file.
  - Reactivate and green all previously skipped tests as part of the refactor.
  - Convert all class-based or skipped tests to function-based, following pytest and Home Assistant best practices.
  - Use clear, descriptive docstrings and ensure all test logic matches the actual config flow/subentry flow implementation.

### Troubleshooting

- **Troubleshooting:**
  - If a test fails due to `UnknownFlow` or similar, verify that the correct flow handler is used and that the test setup matches the integration's actual config flow logic.
  - If main config flow aborts with 'already_configured', this is expected - use SubentryFlows for group/window testing
  - Always check Home Assistant documentation for current SubentryFlow testing patterns

_These rules are based on recent refactoring and bugfixes (2025-08) and should be followed for all future test maintenance._

# Solar Window System Integration Testing Guide (Updated 2025-08-15)

This document describes the testing strategy and implementation for the Home Assistant integration `solar_window_system`, following the latest Home Assistant core and community best practices.

## Table of Contents
1. [Directory & File Structure](#directory--file-structure)
2. [Test Types](#test-types)
3. [Fixtures & Mocks](#fixtures--mocks)
4. [Test Structure & Naming](#test-structure--naming)
5. [Assertions & Error Handling](#assertions--error-handling)
6. [Snapshot Testing](#snapshot-testing)
7. [Running & Debugging Tests](#running--debugging-tests)
8. [Quality Scale Requirements](#quality-scale-requirements)
9. [Best Practices](#best-practices)

---

## Directory & File Structure

- All tests are in `tests/`.
- Use one file per feature/domain (e.g., `test_config_flow.py`, `test_sensor.py`).
- Include `__init__.py` and `conftest.py` for pytest discovery and shared fixtures.
- Example:
    ```
    tests/
        __init__.py
        conftest.py
        test_config_flow.py
        test_entity_creation.py
        test_smoke.py
        ...
    ```

## Test Types

- **Unit tests:** Test individual functions/classes in isolation.
- **Integration tests:** Test the integration with Home Assistant's core interfaces (state machine, config entries, registries).
- **Snapshot tests:** Use `syrupy` to assert large/complex outputs (e.g., diagnostics, entity state).

## Fixtures & Mocks

- Use pytest fixtures for all setup, teardown, and test data.
- Use `MockConfigEntry` for config entry simulation.
- Use `patch`/`AsyncMock` for mocking external dependencies.
- Place all reusable fixtures in `conftest.py`.

## Test Structure & Naming

- Use `@pytest.mark.asyncio` for async tests.
- Prefer function-based tests; use classes only for grouping/parameterization.
- Each test should be independent and self-contained.
- Test functions: `test_<what_is_tested>`.
- Use clear, descriptive docstrings for every test.
- Optionally use the GIVEN-WHEN-THEN pattern for readability.

### Example
```python
@pytest.mark.asyncio
async def test_entity_id_format(hass, global_config_entry):
        """Test that entity IDs follow the required format."""
        # GIVEN: a registered config entry
        # WHEN: the integration is set up
        # THEN: entity IDs are correct
        ...
```

## Assertions & Error Handling

- Assert both positive and negative paths.
- Use `pytest.raises` for error/exception testing.
- For config flows, assert on `result["type"]`, `result["step_id"]`, and data.

### Example
```python
with pytest.raises(Exception) as excinfo:
        await hass.config_entries.options.async_configure(...)
assert "Schema validation failed" in str(excinfo.value)
```

## Snapshot Testing

- Use `syrupy` for diagnostics and entity state snapshots.
- Assert against the `snapshot` fixture.

Short notes for contributors:

- Location: syrupy snapshot files are stored next to the tests under `tests/**/__snapshots__/`.
- Initial generation: run the specific test that uses snapshots with pytest and the `--snapshot-update` flag. Example:

```bash
pytest tests/diagnostics/test_diagnostics.py --snapshot-update
```

- Updating snapshots: only update snapshots when the change to the diagnostics (or other snapshot target) is intentional. Review the diff and commit the updated snapshot(s) alongside the code change.

- Commit message guidance: use a Conventional Commit format. Example:

```
chore(tests): update diagnostics snapshots
```

- CI guidance: do NOT run tests under CI with `--snapshot-update`. CI should run plain `pytest` and fail if snapshots differ from the committed versions. This ensures snapshot regressions are caught in PRs.

### Example
```python
async def test_diagnostics(hass, hass_client, init_integration, snapshot):
    """Test diagnostics output matches the committed snapshot."""
    assert (
        await get_diagnostics_for_config_entry(hass, hass_client, init_integration)
        == snapshot
    )
```

Quick checklist when changing diagnostics output:
1. Run the tests locally with `--snapshot-update` to generate the new snapshot.
2. Inspect the generated files under `tests/**/__snapshots__/` to confirm intended changes.
3. Commit code + snapshots together with an appropriate Conventional Commit message.

## Running & Debugging Tests

- Run all tests: `pytest tests/`
- Run specific test: `pytest tests/test_config_flow.py::test_flow_happy_path`
- Stop on first failure: `pytest -x`
- Run by name: `pytest -k <name>`
- Show slowest tests: `pytest --duration=10`
- Coverage: `pytest --cov=custom_components.solar_window_system --cov-report term-missing`
- Update snapshots: `pytest --snapshot-update`

## Quality Scale Requirements

- **Bronze:** Full config flow test coverage required.
- **Silver:** >95% test coverage for all modules.
- Tests must cover setup, error handling, and all config flows.

## Best Practices

1. **Test Both Paths:** Always test valid and invalid inputs.
2. **Test Boundaries:** Check min/max values and edge cases.
3. **Use Specific Assertions:** Assert on exact values and error messages.
4. **Keep Tests Independent:** No dependencies between tests; use fixtures for setup.
5. **DRY Principle:** Extract common code into fixtures or helpers.
6. **Follow Naming Conventions:** Functions start with `test_`, clear docstrings.
7. **Snapshot Testing:** Use for diagnostics and complex outputs.
8. **Use Core Interfaces:** Prefer Home Assistant's public APIs for setup, state, and registry assertions.

---

For more, see the [Home Assistant Developer Docs: Testing](https://developers.home-assistant.io/docs/development_testing) and [Integration Quality Scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules).

````
