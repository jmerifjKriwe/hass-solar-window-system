"""Tests for group and window related entities.

Assertions are used intentionally; disable S101 for this module.
"""

# ruff: noqa: S101

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN
from custom_components.solar_window_system.sensor import (
    GroupWindowPowerSensor,
    async_setup_entry,
)
from tests.test_data import MOCK_GROUP_SUBENTRIES, MOCK_WINDOW_SUBENTRIES

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


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
    return entry


@pytest.mark.asyncio
async def test_setup_group_power_sensors_creation(
    hass: HomeAssistant, mock_group_config_entry: MockConfigEntry, mock_coordinator
) -> None:
    """Test that group power sensors are created correctly."""
    # Add the config entry to hass (public API).
    mock_group_config_entry.add_to_hass(hass)

    # Populate hass.data using the public hass API so the setup can access
    # the provided mock coordinator during the test.
    hass.data.setdefault(DOMAIN, {})[mock_group_config_entry.entry_id] = {
        "coordinator": mock_coordinator
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

    def mock_add_entities(entities, update_before_add=False, config_subentry_id=None) -> None:
        added_entities.extend(list(entities))

    await async_setup_entry(hass, mock_group_config_entry, mock_add_entities)

    # Expect 2 groups * 3 sensors/group = 6 sensors
    assert len(added_entities) == 6

    # Verify unique IDs and device info for created sensors
    expected_unique_ids = {
        "sws_group_living_room_group_total_power",
        "sws_group_living_room_group_total_power_direct",
        "sws_group_living_room_group_total_power_diffuse",
        "sws_group_bedroom_group_total_power",
        "sws_group_bedroom_group_total_power_direct",
        "sws_group_bedroom_group_total_power_diffuse",
    }

    actual_unique_ids = {entity.unique_id for entity in added_entities}
    assert actual_unique_ids == expected_unique_ids

    # Use identifiers in device_info to derive subentry IDs and assert they exist
    for entity in added_entities:
        assert isinstance(entity, GroupWindowPowerSensor)
        assert entity.device_info is not None
        identifiers = entity.device_info.get("identifiers", set())
        # Find the domain-specific identifier for the group
        domain_ids = [
            i for i in identifiers if i[0] == DOMAIN and i[1].startswith("group_")
        ]
        assert domain_ids, "Expected a domain/group identifier in device_info"
        # Extract and validate the subentry id
    _, full_id = domain_ids[0]
    # Accept any configured subentry key embedded in the identifier string
    assert any(k in full_id for k in mock_group_config_entry.subentries)


@pytest.mark.asyncio
async def test_setup_window_power_sensors_creation(
    hass: HomeAssistant, mock_window_config_entry: MockConfigEntry, mock_coordinator
) -> None:
    """Test that window power sensors are created correctly."""
    mock_window_config_entry.add_to_hass(hass)

    # Populate hass.data so setup can find the injected mock coordinator.
    hass.data.setdefault(DOMAIN, {})[mock_window_config_entry.entry_id] = {
        "coordinator": mock_coordinator
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

    def mock_add_entities(entities, update_before_add=False, config_subentry_id=None) -> None:
        added_entities.extend(list(entities))

    await async_setup_entry(hass, mock_window_config_entry, mock_add_entities)

    # Expect 2 windows * 8 sensors/window = 16 sensors
    assert len(added_entities) == 16

    expected_unique_ids = {
        "sws_window_kitchen_window_total_power",
        "sws_window_kitchen_window_total_power_direct",
        "sws_window_kitchen_window_total_power_diffuse",
        "sws_window_kitchen_window_power_m2_total",
        "sws_window_kitchen_window_power_m2_diffuse",
        "sws_window_kitchen_window_power_m2_direct",
        "sws_window_kitchen_window_power_m2_raw",
        "sws_window_kitchen_window_total_power_raw",
        "sws_window_office_window_total_power",
        "sws_window_office_window_total_power_direct",
        "sws_window_office_window_total_power_diffuse",
        "sws_window_office_window_power_m2_total",
        "sws_window_office_window_power_m2_diffuse",
        "sws_window_office_window_power_m2_direct",
        "sws_window_office_window_power_m2_raw",
        "sws_window_office_window_total_power_raw",
    }

    actual_unique_ids = {entity.unique_id for entity in added_entities}
    assert actual_unique_ids == expected_unique_ids

    # Use identifiers in device_info to derive subentry IDs and assert they exist
    for entity in added_entities:
        assert isinstance(entity, GroupWindowPowerSensor)
        assert entity.device_info is not None
        identifiers = entity.device_info.get("identifiers", set())
        domain_ids = [
            i for i in identifiers if i[0] == DOMAIN and i[1].startswith("window_")
        ]
        assert domain_ids, "Expected a domain/window identifier in device_info"
    _, full_id = domain_ids[0]
    assert any(k in full_id for k in mock_window_config_entry.subentries)
