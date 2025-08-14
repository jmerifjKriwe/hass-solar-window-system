"""Test to specifically verify the str conversion fix."""

import pytest
from unittest.mock import AsyncMock, patch
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN
from custom_components.solar_window_system.options_flow import (
    SolarWindowSystemOptionsFlow,
)


@pytest.mark.asyncio
async def test_group_options_numeric_values_conversion(hass: HomeAssistant) -> None:
    """Test that numeric values from data/options are properly converted to strings in Group Options Flow."""

    # Create a config entry with numeric values as they would be stored
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Group",
        data={
            "entry_type": "group",
            "name": "Test Group",
            "diffuse_factor": 0.15,  # This is a float, not a string
            "threshold_direct": 200,  # This is an int, not a string
            "threshold_diffuse": 150,  # This is an int, not a string
            "temperature_indoor_base": 23.0,  # This is a float, not a string
            "temperature_outdoor_base": 19.5,  # This is a float, not a string
            "indoor_temperature_sensor": "sensor.temp1",  # This is already a string
        },
        options={},
        unique_id="test_group_1",
    )
    config_entry.add_to_hass(hass)

    # Create options flow
    options_flow = SolarWindowSystemOptionsFlow(config_entry)
    options_flow.hass = hass

    # Mock the temperature sensor helper
    with patch(
        "custom_components.solar_window_system.options_flow.get_temperature_sensor_entities"
    ) as mock_temp:
        mock_temp.return_value = [
            {"value": "sensor.temp1", "label": "Temperature 1"},
            {"value": "sensor.temp2", "label": "Temperature 2"},
        ]

        # This should not raise an error - the fix should convert numeric values to strings
        result = await options_flow.async_step_group_options()

        # Verify the schema was created successfully
        assert result["type"] == "form"
        assert result["step_id"] == "group_options"
        assert "data_schema" in result


@pytest.mark.asyncio
async def test_window_options_numeric_values_conversion(hass: HomeAssistant) -> None:
    """Test that numeric values from data/options are properly converted to strings in Window Options Flow."""

    # Create a config entry with numeric values as they would be stored
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Window",
        data={
            "entry_type": "window",
            "name": "Test Window",
            "g_value": 0.5,  # This is a float, not a string
            "frame_width": 0.125,  # This is a float, not a string
            "tilt": 90,  # This is an int, not a string
            "diffuse_factor": 0.15,  # This is a float, not a string
            "threshold_direct": 200,  # This is an int, not a string
            "threshold_diffuse": 150,  # This is an int, not a string
            "temperature_indoor_base": 23.0,  # This is a float, not a string
            "temperature_outdoor_base": 19.5,  # This is a float, not a string
            "indoor_temperature_sensor": "sensor.temp1",  # This is already a string
        },
        options={},
        unique_id="test_window_1",
    )
    config_entry.add_to_hass(hass)

    # Create options flow
    options_flow = SolarWindowSystemOptionsFlow(config_entry)
    options_flow.hass = hass

    # Mock the temperature sensor helper
    with patch(
        "custom_components.solar_window_system.options_flow.get_temperature_sensor_entities"
    ) as mock_temp:
        mock_temp.return_value = [
            {"value": "sensor.temp1", "label": "Temperature 1"},
            {"value": "sensor.temp2", "label": "Temperature 2"},
        ]

        # This should not raise an error - the fix should convert numeric values to strings
        result = await options_flow.async_step_window_options()

        # Verify the schema was created successfully
        assert result["type"] == "form"
        assert result["step_id"] == "window_options"
        assert "data_schema" in result
