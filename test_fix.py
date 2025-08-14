#!/usr/bin/env python3
"""Test script to reproduce and fix the 'expected str' error in options flow."""

import asyncio
from unittest.mock import AsyncMock, patch
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from custom_components.solar_window_system.options_flow import (
    SolarWindowSystemOptionsFlow,
)


async def test_group_options_with_numeric_values():
    """Test Group Options Flow with numeric values stored in data/options."""
    print("Testing Group Options Flow with numeric values...")

    # Mock Home Assistant
    hass = AsyncMock(spec=HomeAssistant)
    hass.config_entries.async_entries.return_value = []

    # Mock config entry with numeric values (as they would be stored)
    config_entry = AsyncMock(spec=ConfigEntry)
    config_entry.data = {
        "entry_type": "group",
        "name": "Test Group",
        "diffuse_factor": 0.15,  # float value
        "threshold_direct": 200,  # int value
        "threshold_diffuse": 150,  # int value
        "temperature_indoor_base": 23.0,  # float value
        "temperature_outdoor_base": 19.5,  # float value
    }
    config_entry.options = {}
    config_entry.domain = "solar_window_system"

    # Create options flow
    options_flow = SolarWindowSystemOptionsFlow()
    options_flow.hass = hass
    options_flow.config_entry = config_entry

    # Mock temperature sensor entities
    with patch(
        "custom_components.solar_window_system.options_flow.get_temperature_sensor_entities"
    ) as mock_temp:
        mock_temp.return_value = [
            {"value": "sensor.temp1", "label": "Temperature 1"},
            {"value": "sensor.temp2", "label": "Temperature 2"},
        ]

        try:
            # This should not raise an error with our fix
            result = await options_flow.async_step_group_options()
            print("✓ Group Options Flow schema creation successful")
            print(f"  Result type: {result.get('type')}")
            return True
        except Exception as e:
            print(f"✗ Group Options Flow failed: {e}")
            return False


async def test_window_options_with_numeric_values():
    """Test Window Options Flow with numeric values stored in data/options."""
    print("Testing Window Options Flow with numeric values...")

    # Mock Home Assistant
    hass = AsyncMock(spec=HomeAssistant)
    hass.config_entries.async_entries.return_value = []

    # Mock config entry with numeric values (as they would be stored)
    config_entry = AsyncMock(spec=ConfigEntry)
    config_entry.data = {
        "entry_type": "window",
        "name": "Test Window",
        "g_value": 0.5,  # float value
        "frame_width": 0.125,  # float value
        "tilt": 90,  # int value
        "diffuse_factor": 0.15,  # float value
        "threshold_direct": 200,  # int value
        "threshold_diffuse": 150,  # int value
        "temperature_indoor_base": 23.0,  # float value
        "temperature_outdoor_base": 19.5,  # float value
        "indoor_temperature_sensor": "sensor.indoor_temp",  # string value
    }
    config_entry.options = {}
    config_entry.domain = "solar_window_system"

    # Create options flow
    options_flow = SolarWindowSystemOptionsFlow()
    options_flow.hass = hass
    options_flow.config_entry = config_entry

    # Mock temperature sensor entities
    with patch(
        "custom_components.solar_window_system.options_flow.get_temperature_sensor_entities"
    ) as mock_temp:
        mock_temp.return_value = [
            {"value": "sensor.temp1", "label": "Temperature 1"},
            {"value": "sensor.temp2", "label": "Temperature 2"},
        ]

        try:
            # This should not raise an error with our fix
            result = await options_flow.async_step_window_options()
            print("✓ Window Options Flow schema creation successful")
            print(f"  Result type: {result.get('type')}")
            return True
        except Exception as e:
            print(f"✗ Window Options Flow failed: {e}")
            return False


async def main():
    """Run all tests."""
    print("Testing options flow with numeric values stored in config...")
    print("=" * 60)

    group_success = await test_group_options_with_numeric_values()
    print()
    window_success = await test_window_options_with_numeric_values()

    print()
    print("=" * 60)
    if group_success and window_success:
        print("✓ All tests passed! The 'expected str' error should be fixed.")
    else:
        print("✗ Some tests failed. The error may still exist.")


if __name__ == "__main__":
    asyncio.run(main())
