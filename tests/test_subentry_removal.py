"""Tests for subentry removal and entity cleanup."""

from types import MappingProxyType
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.solar_window_system import async_on_subentry_removed
from custom_components.solar_window_system.const import (
    DOMAIN,
    ENERGY_TYPE_COMBINED,
    ENERGY_TYPE_DIFFUSE,
    ENERGY_TYPE_DIRECT,
    LEVEL_GROUP,
    LEVEL_WINDOW,
)
from custom_components.solar_window_system.coordinator import (
    SolarCalculationCoordinator,
)


@pytest.fixture
def mock_hass_data(hass):
    """Fixture for mock hass.data setup."""

    # Create mock coordinator
    coordinator = MagicMock(spec=SolarCalculationCoordinator)
    coordinator.groups = {
        "test_group": {
            "name": "Test Group",
            "azimuth": 180,
        }
    }
    coordinator.windows = {}

    # Setup hass.data
    hass.data[DOMAIN] = {
        "test_entry_id": {
            "coordinator": coordinator,
        }
    }

    return hass


async def test_async_on_subentry_removes_group_entities(mock_hass_data):
    """Test that async_on_subentry_removed cleans up group entities and device."""

    hass = mock_hass_data
    entry_id = "test_entry_id"
    subentry_id = "test_group"
    subentry_type = "group"

    # Create and register a real config entry in Home Assistant
    entry = ConfigEntry(
        domain=DOMAIN,
        title="Test Entry",
        data={},
        entry_id=entry_id,
        source="user",
        discovery_keys=MappingProxyType({}),
        minor_version=1,
        options={},
        subentries_data=[],
        unique_id=None,
        version=1,
    )
    hass.config_entries._entries[entry_id] = entry

    # Setup entity registry with mock entities
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)

    # Create a device for the group
    device = device_registry.async_get_or_create(
        config_entry_id=entry_id,
        identifiers={(DOMAIN, f"group_{subentry_id}")},
        name="Gruppe: Test Group",
        manufacturer="Solar Window System",
    )

    # Create mock entities for this group with correct unique_id format
    # Actual format: f"{DOMAIN}_{LEVEL_GROUP}_{subentry_id}_{ENERGY_TYPE_*}"
    entity_unique_ids = [
        f"{DOMAIN}_{LEVEL_GROUP}_{subentry_id}_{ENERGY_TYPE_DIRECT}",
        f"{DOMAIN}_{LEVEL_GROUP}_{subentry_id}_{ENERGY_TYPE_DIFFUSE}",
        f"{DOMAIN}_{LEVEL_GROUP}_{subentry_id}_{ENERGY_TYPE_COMBINED}",
    ]

    entity_entries = []
    for unique_id in entity_unique_ids:
        entry_obj = entity_registry.async_get_or_create(
            domain="sensor",
            platform=DOMAIN,
            unique_id=unique_id,
            config_entry=entry,
            device_id=device.id,
        )
        entity_entries.append(entry_obj)

    # Get actual entity_ids from registry (HA generates these based on name)
    entity_ids = [e.entity_id for e in entity_entries]

    # Verify entities exist before removal
    for entity_id in entity_ids:
        assert entity_registry.async_get(entity_id) is not None

    # Verify device exists
    assert (
        device_registry.async_get_device(identifiers={(DOMAIN, f"group_{subentry_id}")}) is not None
    )

    # Call the removal function
    await async_on_subentry_removed(hass, entry, subentry_id, subentry_type)

    # Verify entities are removed
    for entity_id in entity_ids:
        assert entity_registry.async_get(entity_id) is None

    # Verify device is removed
    assert device_registry.async_get_device(identifiers={(DOMAIN, f"group_{subentry_id}")}) is None

    # Verify coordinator data is cleaned up
    coordinator = hass.data[DOMAIN][entry_id]["coordinator"]
    assert subentry_id not in coordinator.groups


async def test_async_on_subentry_removes_window_entities(mock_hass_data):
    """Test that async_on_subentry_removed cleans up window entities and device."""

    hass = mock_hass_data
    entry_id = "test_entry_id"
    subentry_id = "test_window"
    subentry_type = "window"

    # Setup coordinator with window data
    coordinator = hass.data[DOMAIN][entry_id]["coordinator"]
    coordinator.windows = {
        "test_window": {
            "name": "Test Window",
            "geometry": {"azimuth": 180},
        }
    }
    coordinator.groups = {}

    # Create and register a real config entry in Home Assistant
    entry = ConfigEntry(
        domain=DOMAIN,
        title="Test Entry",
        data={},
        entry_id=entry_id,
        source="user",
        discovery_keys=MappingProxyType({}),
        minor_version=1,
        options={},
        subentries_data=[],
        unique_id=None,
        version=1,
    )
    hass.config_entries._entries[entry_id] = entry

    # Setup registries
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)

    # Create a device for the window
    device = device_registry.async_get_or_create(
        config_entry_id=entry_id,
        identifiers={(DOMAIN, f"window_{subentry_id}")},
        name="Fenster: Test Window",
        manufacturer="Solar Window System",
    )

    # Create mock entities with correct unique_id format
    # Actual format: f"{DOMAIN}_{LEVEL_WINDOW}_{subentry_id}_{ENERGY_TYPE_*}"
    entity_entry = entity_registry.async_get_or_create(
        domain="sensor",
        platform=DOMAIN,
        unique_id=f"{DOMAIN}_{LEVEL_WINDOW}_{subentry_id}_{ENERGY_TYPE_DIRECT}",
        config_entry=entry,
        device_id=device.id,
    )
    entity_id = entity_entry.entity_id

    # Call removal
    await async_on_subentry_removed(hass, entry, subentry_id, subentry_type)

    # Verify cleanup
    assert entity_registry.async_get(entity_id) is None
    assert device_registry.async_get_device(identifiers={(DOMAIN, f"window_{subentry_id}")}) is None
    assert subentry_id not in coordinator.windows


async def test_async_on_subentry_handles_nonexistent_group(mock_hass_data):
    """Test that async_on_subentry_removed handles non-existent group gracefully."""

    hass = mock_hass_data
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.domain = DOMAIN

    # Should not raise exception for non-existent subentry
    await async_on_subentry_removed(hass, entry, "nonexistent_group", "group")

    # Verify no crash occurred
    assert True


async def test_async_on_subentry_handles_missing_coordinator(mock_hass_data):
    """Test that async_on_subentry_removed handles missing coordinator gracefully."""

    hass = mock_hass_data
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "no_coordinator_entry"
    entry.domain = DOMAIN

    # Setup entry without coordinator
    hass.data[DOMAIN]["no_coordinator_entry"] = {}

    # Should not raise exception
    await async_on_subentry_removed(hass, entry, "some_group", "group")

    assert True
