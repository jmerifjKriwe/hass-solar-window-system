# Solar Window System Test Framework

## Overview

This document describes the standardized test framework for the Solar Window System component. The framework provides consistent patterns and base classes to ensure uniformity across all test files.

## Framework Components

### Base Classes

#### `BaseTestCase`
Abstract base class that all test cases should inherit from. Provides common functionality and enforces consistent structure.

#### `ConfigFlowTestCase`
Specialized base class for config flow tests. Includes methods for:
- `init_flow()`: Initialize config flows with standardized parameters
- `submit_form()`: Submit form data with standardized parameters

#### `PlatformTestCase`
Specialized base class for platform tests. Includes methods for:
- `setup_platform_entities()`: Set up platform entities with standardized approach

#### `IntegrationTestCase`
Specialized base class for integration tests. Includes methods for:
- `setup_integration()`: Set up integration with standardized approach

#### `ServiceTestCase`
Specialized base class for service tests. Includes methods for:
- `call_service()`: Call services with standardized parameters

### Test Patterns

#### `TestPatterns`
Collection of standardized assertion methods:
- `assert_config_flow_result()`: Assert config flow results
- `assert_entity_creation()`: Assert entity creation
- `assert_service_registered()`: Assert service registration

## Usage Examples

### Config Flow Tests

```python
from tests.helpers.test_framework import ConfigFlowTestCase, TestPatterns

class TestGlobalConfigFlow(ConfigFlowTestCase):
    """Test global config flow using standardized framework."""

    async def test_init_shows_basic_step(self, hass: HomeAssistant) -> None:
        """Test that config flow initialization shows the basic step."""
        result = await self.init_flow(hass, "user")
        TestPatterns.assert_config_flow_result(result, "form", "global_basic")

    async def test_basic_step_with_valid_data(self, hass: HomeAssistant) -> None:
        """Test basic step with valid configuration data."""
        result = await self.init_flow(hass, "user")
        TestPatterns.assert_config_flow_result(result, "form", "global_basic")

        form_data = {
            "name": "Test System",
            "latitude": 52.52,
            "longitude": 13.405,
            "timezone": "Europe/Berlin"
        }
        result = await self.submit_form(hass, "global_basic", form_data)
        TestPatterns.assert_config_flow_result(result, "form", "global_enhanced")
```

### Platform Tests

```python
from tests.helpers.test_framework import PlatformTestCase, TestPatterns

class TestPlatformEntities(PlatformTestCase):
    """Test platform entity creation using standardized framework."""

    @pytest.mark.parametrize("platform_name,module_path,platform_key", PLATFORMS)
    async def test_entities_creation(self, hass, entity_configs_by_platform,
                                   global_config_entry, platform_name, module_path, platform_key):
        """Test that entities are created correctly for each platform."""
        module = importlib.import_module(module_path)
        entities = await self.setup_platform_entities(hass, module, global_config_entry)
        TestPatterns.assert_entity_creation(entities, len(entity_configs_by_platform[platform_key]), platform_name)
```

### Integration Tests

```python
from tests.helpers.test_framework import IntegrationTestCase

class TestIntegration(IntegrationTestCase):
    """Test integration setup using standardized framework."""

    async def test_integration_setup(self, hass: HomeAssistant, global_config_entry) -> None:
        """Test that integration sets up correctly."""
        await self.setup_integration(hass, global_config_entry)
        # Add specific integration tests here
```

## Migration Guide

### From Old Pattern to New Pattern

#### Old Pattern (Individual Functions)
```python
async def test_global_config_flow_init_shows_basic_step(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result.get("type") == "form"
    assert result.get("step_id") == "global_basic"
```

#### New Pattern (Class-Based)
```python
class TestGlobalConfigFlow(ConfigFlowTestCase):
    async def test_init_shows_basic_step(self, hass: HomeAssistant) -> None:
        result = await self.init_flow(hass, "user")
        TestPatterns.assert_config_flow_result(result, "form", "global_basic")
```

## Benefits

1. **Consistency**: All tests follow the same patterns and structure
2. **Maintainability**: Less code duplication, easier to update patterns
3. **Readability**: Clear, standardized test structure
4. **Extensibility**: Easy to add new test patterns and base classes
5. **Error Reduction**: Standardized patterns reduce human error

## Best Practices

1. Always inherit from the appropriate base class (`ConfigFlowTestCase`, `PlatformTestCase`, etc.)
2. Use `TestPatterns` for assertions instead of raw `assert` statements
3. Follow the naming convention: `Test[Component][Type]`
4. Add docstrings to all test methods explaining what they test
5. Use fixtures appropriately and only include required fixtures in `get_required_fixtures()`

## File Structure

```
tests/
├── helpers/
│   ├── test_framework.py      # Main framework classes and patterns
│   ├── fixtures_helpers.py    # Helper functions for fixtures
│   └── example_test_migration.py  # Examples of migrated tests
├── config_flow/
│   ├── test_config_flow_global.py
│   ├── test_config_flow_window.py
│   └── ...
├── platforms/
│   ├── test_sensor_platform.py
│   ├── test_switch_platform.py
│   └── ...
└── integration/
    ├── test_full_integration.py
    └── ...
```

## Future Enhancements

- Add more specialized base classes for specific test types
- Implement automatic test discovery and registration
- Add performance testing patterns
- Integrate with CI/CD for automated test reporting</content>
<parameter name="filePath">/workspaces/hass-solar-window-system/tests/helpers/README.md
