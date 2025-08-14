"""Test for 'expected str' error in options flow with pre-saved numeric values."""

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN
from custom_components.solar_window_system.options_flow import (
    SolarWindowSystemOptionsFlow,
)


@pytest.mark.asyncio
async def test_group_options_with_presaved_numeric_values(hass: HomeAssistant) -> None:
    """Test that Group Options Flow handles pre-saved numeric values without 'expected str' error."""
    # Create a config entry with numeric values as they would be stored after initial config
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Group",
        data={
            "entry_type": "group",
            "name": "Test Group",
            "diffuse_factor": 0.15,  # This is stored as float
            "threshold_direct": 200,  # This is stored as int
            "threshold_diffuse": 150,  # This is stored as int
            "temperature_indoor_base": 23.0,  # This is stored as float
            "temperature_outdoor_base": 19.5,  # This is stored as float
            "indoor_temperature_sensor": "sensor.temp1",  # String value
        },
        options={},
        unique_id="test_group_1",
    )
    config_entry.add_to_hass(hass)

    # Set up the integration first so options flow can be started
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # This is where the error occurred - during the first step with numeric defaults
    flow_init_result = await hass.config_entries.options.async_init(
        config_entry.entry_id
    )

    # This should show the form without errors
    assert flow_init_result["type"] == "form"
    assert flow_init_result["step_id"] == "group_options"
    assert "data_schema" in flow_init_result

    # Simulate submitting the form with the SAME values that were pre-filled
    # This is the exact scenario where the error occurred - user leaves pre-filled values
    user_input = {
        "name": "Test Group",
        "indoor_temperature_sensor": "sensor.temp1",
        "diffuse_factor": "0.15",  # User sees this as string but it came from float
        "threshold_direct": "200",  # User sees this as string but it came from int
        "threshold_diffuse": "150",  # User sees this as string but it came from int
        "temperature_indoor_base": "23.0",  # User sees this as string but it came from float
        "temperature_outdoor_base": "19.5",  # User sees this as string but it came from float
    }

    # This should NOT raise "expected str" error
    try:
        result = await hass.config_entries.options.async_configure(
            flow_init_result["flow_id"], user_input=user_input
        )
        # Should successfully create the entry
        assert result["type"] == "create_entry"
        assert result["title"] == "Test Group"
        assert "data" in result
    except (ValueError, TypeError, KeyError) as e:
        # If we get here, the fix didn't work
        pytest.fail(f"Options flow failed with error: {e}")


@pytest.mark.asyncio
async def test_group_options_form_shows_correct_defaults(hass: HomeAssistant) -> None:
    """Test that Group Options Flow shows correct default values from pre-saved data."""
    # Create config entry with mixed data types as they would be stored
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Group With Defaults",
        data={
            "entry_type": "group",
            "name": "Test Group With Defaults",
            "diffuse_factor": 0.25,  # float
            "threshold_direct": 300,  # int
            "temperature_indoor_base": 22.5,  # float
            "indoor_temperature_sensor": "sensor.indoor",  # string
        },
        options={
            # Some values in options (these should take precedence)
            "threshold_diffuse": 180,  # int in options
            "temperature_outdoor_base": 20.0,  # float in options
        },
        unique_id="test_group_defaults",
    )
    config_entry.add_to_hass(hass)

    # Set up the integration
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Start options flow - this should create schema with correct defaults
    flow_init_result = await hass.config_entries.options.async_init(
        config_entry.entry_id
    )

    # Verify form is shown
    assert flow_init_result["type"] == "form"
    assert flow_init_result["step_id"] == "group_options"

    # Check that schema was created successfully (no "expected str" error during schema creation)
    schema = flow_init_result["data_schema"]
    assert schema is not None

    # Test empty input (user just clicks OK without changing anything)
    # This should also work without errors
    empty_result = await hass.config_entries.options.async_configure(
        flow_init_result["flow_id"], user_input={}
    )

    # Should show validation errors for required fields, not "expected str"
    assert empty_result["type"] == "form"  # Form shown again with errors
    assert "errors" in empty_result
    # Should have validation errors for required fields
    assert "name" in empty_result["errors"]
    assert "indoor_temperature_sensor" in empty_result["errors"]


@pytest.mark.asyncio
async def test_window_options_with_presaved_numeric_values(hass: HomeAssistant) -> None:
    """Test that Window Options Flow handles pre-saved numeric values without 'expected str' error."""
    # Create a config entry with numeric values for window
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Window",
        data={
            "entry_type": "window",
            "name": "Test Window",
            "g_value": 0.6,  # float
            "frame_width": 0.15,  # float
            "tilt": 85,  # int
            "diffuse_factor": 0.2,  # float
            "threshold_direct": 250,  # int
            "threshold_diffuse": 175,  # int
            "temperature_indoor_base": 24.0,  # float
            "temperature_outdoor_base": 18.5,  # float
            "indoor_temperature_sensor": "sensor.window_temp",  # string
        },
        options={},
        unique_id="test_window_1",
    )
    config_entry.add_to_hass(hass)

    # Set up the integration
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Start options flow
    flow_init_result = await hass.config_entries.options.async_init(
        config_entry.entry_id
    )

    # Should show form without errors
    assert flow_init_result["type"] == "form"
    assert flow_init_result["step_id"] == "window_options"
    assert "data_schema" in flow_init_result

    # Submit with pre-filled values (this is where the error occurred)
    user_input = {
        "name": "Test Window",
        "indoor_temperature_sensor": "sensor.window_temp",
        "g_value": "0.6",  # These come from the UI as strings
        "frame_width": "0.15",
        "tilt": "85",
        "diffuse_factor": "0.2",
        "threshold_direct": "250",
        "threshold_diffuse": "175",
        "temperature_indoor_base": "24.0",
        "temperature_outdoor_base": "18.5",
    }

    # This should NOT raise "expected str" error
    try:
        result = await hass.config_entries.options.async_configure(
            flow_init_result["flow_id"], user_input=user_input
        )
        assert result["type"] == "create_entry"
        assert result["title"] == "Test Window"
    except (ValueError, TypeError, KeyError) as e:
        pytest.fail(f"Window options flow failed with error: {e}")


@pytest.mark.asyncio
async def test_group_options_with_edge_case_numeric_values(hass: HomeAssistant) -> None:
    """Test edge cases like negative values, zero, very small numbers."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Edge Case Group",
        data={
            "entry_type": "group",
            "name": "Edge Case Group",
            "diffuse_factor": 0.001,  # Very small float
            "threshold_direct": 0,  # Zero
            "threshold_diffuse": -1,  # Negative (sentinel value)
            "temperature_indoor_base": -5.5,  # Negative float
            "temperature_outdoor_base": 100.99999,  # Large precise float
            "indoor_temperature_sensor": "sensor.edge",
        },
        options={},
        unique_id="test_group_edge",
    )
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    flow_init_result = await hass.config_entries.options.async_init(
        config_entry.entry_id
    )

    # Verify form initialization works with edge case values
    assert flow_init_result["type"] == "form"
    assert flow_init_result["step_id"] == "group_options"

    # Test submission with edge case values converted to strings
    user_input = {
        "name": "Edge Case Group",
        "indoor_temperature_sensor": "sensor.edge",
        "diffuse_factor": "0.001",
        "threshold_direct": "0",
        "threshold_diffuse": "-1",
        "temperature_indoor_base": "-5.5",
        "temperature_outdoor_base": "100.99999",
    }

    result = await hass.config_entries.options.async_configure(
        flow_init_result["flow_id"], user_input=user_input
    )
    assert result["type"] == "create_entry"


if __name__ == "__main__":
    # This allows running the test directly for debugging
    pass  # Test runner will handle execution
