"""Tests for config flow with checkbox-based optional sensor handling."""

from unittest.mock import MagicMock, patch

import pytest

from custom_components.solar_window_system.config_flow import ConfigFlow
from custom_components.solar_window_system.const import (
    CONF_G_VALUE,
    CONF_IRRADIANCE_DIFFUSE_SENSOR,
    CONF_IRRADIANCE_SENSOR,
    CONF_PROPERTIES,
    CONF_SENSORS,
    CONF_TEMP_INDOOR,
    CONF_TEMP_OUTDOOR,
    CONF_USE_IRRADIANCE_DIFFUSE,
    CONF_USE_TEMP_INDOOR,
    CONF_USE_TEMP_OUTDOOR,
    CONF_USE_WEATHER_CONDITION,
    CONF_USE_WEATHER_WARNING,
    CONF_WEATHER_CONDITION,
    CONF_WEATHER_WARNING,
    DEFAULT_G_VALUE,
    DOMAIN,
)


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry with initial sensors."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {
        "name": "Test Solar System",
        CONF_SENSORS: {
            CONF_IRRADIANCE_SENSOR: "sensor.irradiance",
            CONF_IRRADIANCE_DIFFUSE_SENSOR: "sensor.irradiance_diffuse",
            CONF_TEMP_OUTDOOR: "sensor.temp_outdoor",
            CONF_TEMP_INDOOR: "sensor.temp_indoor",
            CONF_WEATHER_WARNING: "binary_sensor.weather_warning",
            CONF_WEATHER_CONDITION: "sensor.weather_condition",
        },
        CONF_PROPERTIES: {
            CONF_G_VALUE: 0.75,
        },
    }
    return entry


@pytest.mark.asyncio
async def test_reconfigure_checkbox_removes_sensor():
    """Test that unchecking a sensor checkbox removes the sensor.

    This tests the checkbox-based removal:
    1. User opens reconfigure
    2. User unchecks the checkbox for an optional sensor
    3. User saves
    4. The sensor is removed from the saved data
    """
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {
        "name": "Test Solar System",
        CONF_SENSORS: {
            CONF_IRRADIANCE_SENSOR: "sensor.irradiance",
            CONF_TEMP_INDOOR: "sensor.temp_indoor",
        },
        CONF_PROPERTIES: {
            CONF_G_VALUE: 0.75,
        },
    }

    flow = ConfigFlow()
    flow.hass = MagicMock()

    with patch.object(flow, "_get_reconfigure_entry", return_value=entry):
        # User unchecks temp_indoor checkbox but keeps the entity value
        user_input = {
            "name": "Test Solar System",
            CONF_IRRADIANCE_SENSOR: "sensor.irradiance",
            CONF_USE_TEMP_INDOOR: False,  # Checkbox unchecked = remove sensor
            CONF_TEMP_INDOOR: "sensor.temp_indoor",  # Entity still has value
            CONF_USE_TEMP_OUTDOOR: False,  # Checkbox unchecked = remove sensor
            CONF_TEMP_OUTDOOR: "sensor.temp_outdoor",
            CONF_USE_IRRADIANCE_DIFFUSE: False,
            CONF_IRRADIANCE_DIFFUSE_SENSOR: None,
            CONF_USE_WEATHER_WARNING: False,
            CONF_WEATHER_WARNING: None,
            CONF_USE_WEATHER_CONDITION: False,
            CONF_WEATHER_CONDITION: None,
            CONF_PROPERTIES: {
                CONF_G_VALUE: 0.75,
            },
        }

        captured_updates = {}

        def mock_update_reload_and_abort(entry_obj, data_updates):
            captured_updates["data"] = data_updates
            return MagicMock()

        with patch.object(
            flow, "async_update_reload_and_abort", side_effect=mock_update_reload_and_abort
        ):
            await flow.async_step_reconfigure(user_input)

        updated_sensors = captured_updates["data"][CONF_SENSORS]
        print(f"Updated sensors after checkbox uncheck: {updated_sensors}")

        # Unchecked sensor should be removed
        assert CONF_TEMP_INDOOR not in updated_sensors

        # Required sensor should still be there
        assert CONF_IRRADIANCE_SENSOR in updated_sensors


@pytest.mark.asyncio
async def test_reconfigure_checkbox_keeps_sensor():
    """Test that checked checkbox keeps the sensor."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {
        "name": "Test Solar System",
        CONF_SENSORS: {
            CONF_IRRADIANCE_SENSOR: "sensor.irradiance",
            CONF_TEMP_INDOOR: "sensor.temp_indoor",
        },
        CONF_PROPERTIES: {
            CONF_G_VALUE: 0.75,
        },
    }

    flow = ConfigFlow()
    flow.hass = MagicMock()

    with patch.object(flow, "_get_reconfigure_entry", return_value=entry):
        # User keeps temp_indoor checkbox checked
        user_input = {
            "name": "Test Solar System",
            CONF_IRRADIANCE_SENSOR: "sensor.irradiance",
            CONF_USE_TEMP_INDOOR: True,  # Checkbox checked = keep sensor
            CONF_TEMP_INDOOR: "sensor.temp_indoor",
            CONF_USE_TEMP_OUTDOOR: True,  # Checkbox checked = keep sensor
            CONF_TEMP_OUTDOOR: "sensor.temp_outdoor",
            CONF_USE_IRRADIANCE_DIFFUSE: False,
            CONF_IRRADIANCE_DIFFUSE_SENSOR: None,
            CONF_USE_WEATHER_WARNING: False,
            CONF_WEATHER_WARNING: None,
            CONF_USE_WEATHER_CONDITION: False,
            CONF_WEATHER_CONDITION: None,
            CONF_PROPERTIES: {
                CONF_G_VALUE: 0.75,
            },
        }

        captured_updates = {}

        def mock_update_reload_and_abort(entry_obj, data_updates):
            captured_updates["data"] = data_updates
            return MagicMock()

        with patch.object(
            flow, "async_update_reload_and_abort", side_effect=mock_update_reload_and_abort
        ):
            await flow.async_step_reconfigure(user_input)

        updated_sensors = captured_updates["data"][CONF_SENSORS]
        print(f"Updated sensors with checkbox checked: {updated_sensors}")

        # Checked sensor should be kept
        assert CONF_TEMP_INDOOR in updated_sensors
        assert updated_sensors[CONF_TEMP_INDOOR] == "sensor.temp_indoor"


@pytest.mark.asyncio
async def test_reconfigure_validation_error_when_checkbox_no_entity():
    """Test that validation fails when checkbox is checked but no entity selected."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {
        "name": "Test Solar System",
        CONF_SENSORS: {
            CONF_IRRADIANCE_SENSOR: "sensor.irradiance",
        },
        CONF_PROPERTIES: {},
    }

    flow = ConfigFlow()
    flow.hass = MagicMock()

    with patch.object(flow, "_get_reconfigure_entry", return_value=entry):
        # User checks checkbox but doesn't select entity
        user_input = {
            "name": "Test Solar System",
            CONF_IRRADIANCE_SENSOR: "sensor.irradiance",
            CONF_USE_TEMP_INDOOR: True,  # Checkbox checked
            CONF_TEMP_INDOOR: None,  # But no entity selected!
            CONF_USE_TEMP_OUTDOOR: True,  # Checkbox checked
            CONF_TEMP_OUTDOOR: "sensor.temp_outdoor",
            CONF_USE_IRRADIANCE_DIFFUSE: False,
            CONF_IRRADIANCE_DIFFUSE_SENSOR: None,
            CONF_USE_WEATHER_WARNING: False,
            CONF_WEATHER_WARNING: None,
            CONF_USE_WEATHER_CONDITION: False,
            CONF_WEATHER_CONDITION: None,
            CONF_PROPERTIES: {
                CONF_G_VALUE: DEFAULT_G_VALUE,
            },
        }

        result = await flow.async_step_reconfigure(user_input)

        # Should return form with errors, not update entry
        assert "errors" in result
        errors = result.get("errors")
        assert errors is not None
        assert errors.get(CONF_TEMP_INDOOR) == "missing_entity_for_enabled_sensor"


@pytest.mark.asyncio
async def test_reconfigure_validation_error_empty_string():
    """Test that validation fails when checkbox is checked but entity is empty string."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {
        "name": "Test Solar System",
        CONF_SENSORS: {
            CONF_IRRADIANCE_SENSOR: "sensor.irradiance",
        },
        CONF_PROPERTIES: {},
    }

    flow = ConfigFlow()
    flow.hass = MagicMock()

    with patch.object(flow, "_get_reconfigure_entry", return_value=entry):
        # User checks checkbox but entity is empty string
        user_input = {
            "name": "Test Solar System",
            CONF_IRRADIANCE_SENSOR: "sensor.irradiance",
            CONF_USE_TEMP_INDOOR: True,  # Checkbox checked
            CONF_TEMP_INDOOR: "",  # Empty string - invalid!
            CONF_USE_TEMP_OUTDOOR: True,  # Checkbox checked
            CONF_TEMP_OUTDOOR: "sensor.temp_outdoor",
            CONF_USE_IRRADIANCE_DIFFUSE: False,
            CONF_IRRADIANCE_DIFFUSE_SENSOR: None,
            CONF_USE_WEATHER_WARNING: False,
            CONF_WEATHER_WARNING: None,
            CONF_USE_WEATHER_CONDITION: False,
            CONF_WEATHER_CONDITION: None,
            CONF_PROPERTIES: {
                CONF_G_VALUE: DEFAULT_G_VALUE,
            },
        }

        result = await flow.async_step_reconfigure(user_input)

        # Should return form with errors
        assert "errors" in result
        errors = result.get("errors")
        assert errors is not None
        assert errors.get(CONF_TEMP_INDOOR) == "missing_entity_for_enabled_sensor"


@pytest.mark.asyncio
async def test_reconfigure_form_has_checkbox_defaults():
    """Test that the reconfigure form has correct checkbox defaults based on current config."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {
        "name": "Test Solar System",
        CONF_SENSORS: {
            CONF_IRRADIANCE_SENSOR: "sensor.irradiance",
            CONF_TEMP_INDOOR: "sensor.temp_indoor",  # This sensor is configured
            # TEMP_OUTDOOR is NOT configured
        },
        CONF_PROPERTIES: {
            CONF_G_VALUE: 0.75,
        },
    }

    flow = ConfigFlow()
    flow.hass = MagicMock()

    with patch.object(flow, "_get_reconfigure_entry", return_value=entry):
        result = await flow.async_step_reconfigure(user_input=None)

    schema = result.get("data_schema")
    assert schema is not None

    # Find checkbox defaults
    checkbox_defaults = {}
    for key in schema.schema.keys():
        if hasattr(key, "schema"):
            key_name = key.schema
            if key_name.startswith("use_"):
                default_val = key.default
                if callable(default_val):
                    default_val = default_val()
                checkbox_defaults[key_name] = default_val

    print(f"Checkbox defaults: {checkbox_defaults}")

    # Configured sensors should have checked checkboxes (True)
    assert checkbox_defaults.get(CONF_USE_TEMP_INDOOR) is True

    # Not configured sensors should have unchecked checkboxes (False)
    assert checkbox_defaults.get(CONF_USE_WEATHER_WARNING) is False
    assert checkbox_defaults.get(CONF_USE_TEMP_OUTDOOR) is False


@pytest.mark.asyncio
async def test_reconfigure_adds_new_optional_sensor():
    """Test that a new optional sensor can be added via reconfigure."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {
        "name": "Test Solar System",
        CONF_SENSORS: {
            CONF_IRRADIANCE_SENSOR: "sensor.irradiance",
            # No optional sensors yet
        },
        CONF_PROPERTIES: {},
    }

    flow = ConfigFlow()
    flow.hass = MagicMock()

    with patch.object(flow, "_get_reconfigure_entry", return_value=entry):
        # User adds temp_indoor sensor
        user_input = {
            "name": "Test Solar System",
            CONF_IRRADIANCE_SENSOR: "sensor.irradiance",
            CONF_USE_TEMP_INDOOR: True,  # Enable sensor
            CONF_TEMP_INDOOR: "sensor.temp_indoor_new",  # Select entity
            CONF_USE_TEMP_OUTDOOR: True,  # Enable sensor
            CONF_TEMP_OUTDOOR: "sensor.temp_outdoor",
            CONF_USE_IRRADIANCE_DIFFUSE: False,
            CONF_IRRADIANCE_DIFFUSE_SENSOR: None,
            CONF_USE_WEATHER_WARNING: False,
            CONF_WEATHER_WARNING: None,
            CONF_USE_WEATHER_CONDITION: False,
            CONF_WEATHER_CONDITION: None,
            CONF_PROPERTIES: {
                CONF_G_VALUE: DEFAULT_G_VALUE,
            },
        }

        captured_updates = {}

        def mock_update_reload_and_abort(entry_obj, data_updates):
            captured_updates["data"] = data_updates
            return MagicMock()

        with patch.object(
            flow, "async_update_reload_and_abort", side_effect=mock_update_reload_and_abort
        ):
            await flow.async_step_reconfigure(user_input)

        updated_sensors = captured_updates["data"][CONF_SENSORS]
    print(f"Updated sensors after adding new sensor: {updated_sensors}")

    # New sensor should be added
    assert CONF_TEMP_INDOOR in updated_sensors
    assert updated_sensors[CONF_TEMP_INDOOR] == "sensor.temp_indoor_new"


@pytest.mark.asyncio
async def test_reconfigure_properties_persisted():
    """Test that reconfigure properly saves property values."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {
        "name": "Test Solar System",
        CONF_SENSORS: {
            CONF_IRRADIANCE_SENSOR: "sensor.irradiance",
        },
        CONF_PROPERTIES: {
            CONF_G_VALUE: 0.75,
        },
    }

    flow = ConfigFlow()
    flow.hass = MagicMock()

    with patch.object(flow, "_get_reconfigure_entry", return_value=entry):
        user_input = {
            "name": "Test Solar System",
            CONF_IRRADIANCE_SENSOR: "sensor.irradiance",
            CONF_USE_TEMP_INDOOR: False,
            CONF_TEMP_INDOOR: None,
            CONF_USE_TEMP_OUTDOOR: True,
            CONF_TEMP_OUTDOOR: "sensor.temp_outdoor",
            CONF_USE_IRRADIANCE_DIFFUSE: False,
            CONF_IRRADIANCE_DIFFUSE_SENSOR: None,
            CONF_USE_WEATHER_WARNING: False,
            CONF_WEATHER_WARNING: None,
            CONF_USE_WEATHER_CONDITION: False,
            CONF_WEATHER_CONDITION: None,
            CONF_PROPERTIES: {
                CONF_G_VALUE: 0.85,  # Changed from 0.75 to 0.85
            },
        }

        captured_updates = {}

        def mock_update_reload_and_abort(entry_obj, data_updates):
            captured_updates["data"] = data_updates
            return MagicMock()

        with patch.object(
            flow, "async_update_reload_and_abort", side_effect=mock_update_reload_and_abort
        ):
            await flow.async_step_reconfigure(user_input)

        # Verify property was updated
        updated_properties = captured_updates["data"][CONF_PROPERTIES]
        assert updated_properties[CONF_G_VALUE] == 0.85


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
