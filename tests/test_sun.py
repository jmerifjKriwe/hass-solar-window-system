"""Tests for the Solar Window System integration."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN


MOCK_CONFIG_DATA = {
    "defaults": {"temperatures": {"indoor_base": 21, "outdoor_base": 16}},
    "groups": {},
    "windows": {
        f"window_{i}": {
            "name": f"Window {i}",
            "room_temp_entity": f"sensor.dummy_temperatur_raum_{i}",
        }
        for i in range(21)
    },
}

MOCK_USER_INPUT = {
    "solar_radiation_sensor": "sensor.dummy_solar_radiation_sensor",
    "outdoor_temperature_sensor": "sensor.dummy_outdoor_temperature_sensor",
}


@pytest.mark.asyncio
async def test_successful_setup(hass):
    """Test that the integration setup loads successfully."""

    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_INPUT)
    entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.solar_window_system._load_config_from_files",
            return_value=MOCK_CONFIG_DATA,
        ),
        patch(
            "custom_components.solar_window_system.SolarWindowDataUpdateCoordinator"
        ) as MockCoordinator,
        patch(
            "custom_components.solar_window_system._register_services",
            new_callable=AsyncMock,
        ),
        patch(
            "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
            new_callable=AsyncMock,
        ),
    ):
        # Setup MockCoordinator instance and its async methods
        instance = MockCoordinator.return_value
        instance.async_config_entry_first_refresh = AsyncMock()
        instance.async_refresh = AsyncMock()

        # Run the config entry setup
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        # Check if the config entry ended up loaded
        assert entry.state == ConfigEntryState.LOADED
        # Check if coordinator is stored in hass.data correctly
        assert DOMAIN in hass.data
        assert entry.entry_id in hass.data[DOMAIN]
        assert hass.data[DOMAIN][entry.entry_id] is instance
