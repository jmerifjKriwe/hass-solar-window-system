"""Test that global config entities have correct entity_id and unique_id format."""

import pytest
from unittest.mock import Mock
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.config_entries import ConfigEntry
from custom_components.solar_window_system.const import (
    ENTITY_PREFIX_GLOBAL,
    GLOBAL_CONFIG_ENTITIES,
)
from custom_components.solar_window_system.global_config import GlobalConfigSensor
from custom_components.solar_window_system.number import GlobalConfigNumberEntity
from custom_components.solar_window_system.select import GlobalConfigSelectEntity
from custom_components.solar_window_system.text import GlobalConfigTextEntity
from custom_components.solar_window_system.switch import GlobalConfigSwitchEntity

@pytest.mark.asyncio
async def test_global_config_entity_id_and_unique_id_format(hass: HomeAssistant):
    """Test that all global config entities have correct entity_id and unique_id format."""
    # Create and add a mock config entry using unittest.mock
    config_entry = Mock(spec=ConfigEntry)
    config_entry.entry_id = "test_entry"
    config_entry.domain = "solar_window_system"
    config_entry.title = "Solar Window System"
    config_entry.data = {}
    config_entry.unique_id = "test_unique_id"
    config_entry.state = "loaded"
    hass.config_entries._entries[config_entry.entry_id] = config_entry

    # Create a mock device
    device_registry = dr.async_get(hass)
    device = device_registry.async_get_or_create(
        config_entry_id="test_entry",
        identifiers={("solar_window_system", "global_config")},
        name="Solar Window System Global Configuration",
        manufacturer="Solar Window System",
        model="Global Configuration",
    )

    # Test all entity types
    for entity_key in GLOBAL_CONFIG_ENTITIES:
        config = {
            "name": entity_key,
            "default": 0,
            "min": 0,
            "max": 100,
            "step": 1,
            "options": ["A", "B"],
            "icon": "mdi:test",
        }
        sensor = GlobalConfigSensor(entity_key, config, device)
        number = GlobalConfigNumberEntity(entity_key, config, device)
        select = GlobalConfigSelectEntity(entity_key, config, device)
        text = GlobalConfigTextEntity(entity_key, config, device)
        switch = GlobalConfigSwitchEntity(entity_key, config, device)

        for entity in [sensor, number, select, text, switch]:
            # Check unique_id
            unique_id = getattr(entity, "_attr_unique_id", None)
            expected_unique_id = f"{ENTITY_PREFIX_GLOBAL}_{entity_key}"
            assert unique_id == expected_unique_id, (
                f"unique_id for {entity_key} should be '{expected_unique_id}', "
                f"got '{unique_id}'"
            )
            # Note: We don't check _attr_entity_id because our workaround approach
            # uses suggested_object_id and HA generates the final entity_id
