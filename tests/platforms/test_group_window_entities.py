"""Tests for group and window related entities."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN, ENTITY_PREFIX
from tests.test_data import MOCK_GROUP_SUBENTRIES, MOCK_WINDOW_SUBENTRIES
from custom_components.solar_window_system.sensor import (
    async_setup_entry,
    GroupWindowPowerSensor,
    SolarWindowSystemGroupDummySensor,
)


@pytest.fixture
def mock_coordinator():
    """Fixture for a mock DataUpdateCoordinator."""
    coordinator = AsyncMock(spec=DataUpdateCoordinator)
    coordinator.data = {}  # Initialize with empty data
    return coordinator


@pytest.fixture
def mock_group_config_entry(mock_coordinator):
    """Fixture for a mock ConfigEntry for group configurations."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Group Config",
        data={"entry_type": "group_configs"},
        entry_id="test_group_entry",
    )
    # Use shared subentry mocks
    entry.subentries = {k: Mock(**v) for k, v in MOCK_GROUP_SUBENTRIES.items()}
    entry.hass_data = {"coordinator": mock_coordinator}
    return entry


@pytest.fixture
def mock_window_config_entry(mock_coordinator):
    """Fixture for a mock ConfigEntry for window configurations."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Window Config",
        data={"entry_type": "window_configs"},
        entry_id="test_window_entry",
    )
    # Use shared subentry mocks
    entry.subentries = {k: Mock(**v) for k, v in MOCK_WINDOW_SUBENTRIES.items()}
    entry.hass_data = {"coordinator": mock_coordinator}
    return entry


@pytest.mark.asyncio
async def test_setup_group_power_sensors_creation(
    hass: HomeAssistant, mock_group_config_entry: MockConfigEntry
):
    """Test that group power sensors are created correctly."""
    # Add the config entry to hass
    mock_group_config_entry.add_to_hass(hass)
    hass.data[DOMAIN] = {
        mock_group_config_entry.entry_id: mock_group_config_entry.hass_data
    }

    # Create mock devices in device registry for the subentries
    dev_reg = dr.async_get(hass)
    for subentry_id, subentry in mock_group_config_entry.subentries.items():
        dev_reg.async_get_or_create(
            config_entry_id=mock_group_config_entry.entry_id,
            config_subentry_id=subentry_id,
            identifiers={(DOMAIN, f"group_{subentry_id}")},
            name=subentry.title,
            manufacturer="Solar Window System",
            model="Group",
        )

    # Track added entities
    added_entities = []

    def mock_add_entities(entities, update_before_add=False, config_subentry_id=None):
        added_entities.extend(list(entities))

    await async_setup_entry(hass, mock_group_config_entry, mock_add_entities)

    # Expect 2 groups * 3 sensors/group = 6 sensors
    assert len(added_entities) == 6

    # Verify unique IDs and device info for created sensors
    expected_unique_ids = {
        f"sws_group_living_room_group_total_power",
        f"sws_group_living_room_group_total_power_direct",
        f"sws_group_living_room_group_total_power_diffuse",
        f"sws_group_bedroom_group_total_power",
        f"sws_group_bedroom_group_total_power_direct",
        f"sws_group_bedroom_group_total_power_diffuse",
    }

    actual_unique_ids = {entity.unique_id for entity in added_entities}
    assert actual_unique_ids == expected_unique_ids

    # Map object_name to subentry_id for identifier check
    name_to_id = {
        subentry.title: subentry_id
        for subentry_id, subentry in mock_group_config_entry.subentries.items()
    }
    for entity in added_entities:
        assert isinstance(entity, GroupWindowPowerSensor)
        assert entity.device_info is not None
        subentry_id = name_to_id[entity._object_name]
        assert (DOMAIN, f"group_{subentry_id}") in entity.device_info["identifiers"]


@pytest.mark.asyncio
async def test_setup_window_power_sensors_creation(
    hass: HomeAssistant, mock_window_config_entry: MockConfigEntry
):
    """Test that window power sensors are created correctly."""
    mock_window_config_entry.add_to_hass(hass)
    hass.data[DOMAIN] = {
        mock_window_config_entry.entry_id: mock_window_config_entry.hass_data
    }

    dev_reg = dr.async_get(hass)
    for subentry_id, subentry in mock_window_config_entry.subentries.items():
        dev_reg.async_get_or_create(
            config_entry_id=mock_window_config_entry.entry_id,
            config_subentry_id=subentry_id,
            identifiers={(DOMAIN, f"window_{subentry_id}")},
            name=subentry.title,
            manufacturer="Solar Window System",
            model="Window",
        )

    added_entities = []

    def mock_add_entities(entities, update_before_add=False, config_subentry_id=None):
        added_entities.extend(list(entities))

    await async_setup_entry(hass, mock_window_config_entry, mock_add_entities)

    # Expect 2 windows * 8 sensors/window = 16 sensors
    assert len(added_entities) == 16

    expected_unique_ids = {
        f"sws_window_kitchen_window_total_power",
        f"sws_window_kitchen_window_total_power_direct",
        f"sws_window_kitchen_window_total_power_diffuse",
        f"sws_window_kitchen_window_power_m2_total",
        f"sws_window_kitchen_window_power_m2_diffuse",
        f"sws_window_kitchen_window_power_m2_direct",
        f"sws_window_kitchen_window_power_m2_raw",
        f"sws_window_kitchen_window_total_power_raw",
        f"sws_window_office_window_total_power",
        f"sws_window_office_window_total_power_direct",
        f"sws_window_office_window_total_power_diffuse",
        f"sws_window_office_window_power_m2_total",
        f"sws_window_office_window_power_m2_diffuse",
        f"sws_window_office_window_power_m2_direct",
        f"sws_window_office_window_power_m2_raw",
        f"sws_window_office_window_total_power_raw",
    }

    actual_unique_ids = {entity.unique_id for entity in added_entities}
    assert actual_unique_ids == expected_unique_ids

    # Map object_name to subentry_id for identifier check
    name_to_id = {
        subentry.title: subentry_id
        for subentry_id, subentry in mock_window_config_entry.subentries.items()
    }
    for entity in added_entities:
        assert isinstance(entity, GroupWindowPowerSensor)
        assert entity.device_info is not None
        subentry_id = name_to_id[entity._object_name]
        assert (DOMAIN, f"window_{subentry_id}") in entity.device_info["identifiers"]
