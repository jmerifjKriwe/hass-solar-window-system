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


@pytest.mark.asyncio
async def test_setup_power_sensors_no_subentries(
    hass: HomeAssistant, mock_coordinator: AsyncMock
):
    """Test that no power sensors are created if no subentries exist."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Empty Config",
        data={"entry_type": "group_configs"},
        entry_id="test_empty_entry",
    )
    entry.subentries = {}  # No subentries
    entry.add_to_hass(hass)
    hass.data[DOMAIN] = {entry.entry_id: {"coordinator": mock_coordinator}}

    added_entities = []

    async def mock_add_entities(
        entities, update_before_add=False, config_subentry_id=None
    ):
        added_entities.extend(list(entities))

    await async_setup_entry(hass, entry, mock_add_entities)

    assert len(added_entities) == 0


@pytest.mark.asyncio
async def test_setup_power_sensors_device_not_found(
    hass: HomeAssistant, mock_group_config_entry: MockConfigEntry
):
    """Test that power sensors are not created if the device is not found."""
    mock_group_config_entry.add_to_hass(hass)
    hass.data[DOMAIN] = {
        mock_group_config_entry.entry_id: mock_group_config_entry.hass_data
    }

    # DO NOT create devices in device registry, simulating device not found

    added_entities = []

    async def mock_add_entities(
        entities, update_before_add=False, config_subentry_id=None
    ):
        added_entities.extend(list(entities))

    await async_setup_entry(hass, mock_group_config_entry, mock_add_entities)

    assert len(added_entities) == 0


@pytest.mark.asyncio
async def test_group_window_power_sensor_state_from_coordinator_group(
    hass: HomeAssistant, mock_coordinator: AsyncMock
):
    """Test that GroupWindowPowerSensor gets state from coordinator data for groups."""
    mock_coordinator.data = {
        "groups": {
            "group_id_1": {"name": "Living Room Group", "total_power": 100.5},
            "group_id_2": {"name": "Bedroom Group", "total_power": 50.2},
        }
    }
    mock_device = Mock(spec=dr.DeviceEntry)
    mock_device.identifiers = {(DOMAIN, "group_living_room_group")}
    mock_device.name = "Living Room Group"
    mock_device.manufacturer = "Solar Window System"
    mock_device.model = "Group"

    sensor = GroupWindowPowerSensor(
        kind="group",
        object_name="Living Room Group",
        device=mock_device,
        key="total_power",
        label="Total Power",
        coordinator=mock_coordinator,
    )
    sensor.hass = hass  # Assign hass for state property
    assert sensor.state == 100.5


@pytest.mark.asyncio
async def test_group_window_power_sensor_state_from_coordinator_window(
    hass: HomeAssistant, mock_coordinator: AsyncMock
):
    """Test that GroupWindowPowerSensor gets state from coordinator data for windows."""
    mock_coordinator.data = {
        "windows": {
            "window_id_1": {"name": "Kitchen Window", "total_power": 75.0},
            "window_id_2": {"name": "Office Window", "total_power": 120.0},
        }
    }
    mock_device = Mock(spec=dr.DeviceEntry)
    mock_device.identifiers = {(DOMAIN, "window_kitchen_window")}
    mock_device.name = "Kitchen Window"
    mock_device.manufacturer = "Solar Window System"
    mock_device.model = "Window"

    sensor = GroupWindowPowerSensor(
        kind="window",
        object_name="Kitchen Window",
        device=mock_device,
        key="total_power",
        label="Total Power",
        coordinator=mock_coordinator,
    )
    sensor.hass = hass  # Assign hass for state property
    assert sensor.state == 75.0


@pytest.mark.asyncio
async def test_group_window_power_sensor_state_restoration_no_coordinator_data(
    hass: HomeAssistant, mock_coordinator: AsyncMock
):
    """Test that GroupWindowPowerSensor restores state if no coordinator data."""
    mock_coordinator.data = None  # No data from coordinator

    mock_device = Mock(spec=dr.DeviceEntry)
    mock_device.identifiers = {(DOMAIN, "group_test")}
    mock_device.name = "Test Group"
    mock_device.manufacturer = "Solar Window System"
    mock_device.model = "Group"

    sensor = GroupWindowPowerSensor(
        kind="group",
        object_name="Test Group",
        device=mock_device,
        key="total_power",
        label="Total Power",
        coordinator=mock_coordinator,
    )
    sensor.hass = hass

    # Patch async_added_to_hass to restore state
    async def restore_state_patch(self):
        restored_state = await self.async_get_last_state()
        if restored_state is not None:
            try:
                self._restored_state = float(restored_state.state)
            except (ValueError, TypeError):
                self._restored_state = None

    with patch.object(
        sensor, "async_get_last_state", AsyncMock(return_value=Mock(state="99.9"))
    ):
        with patch.object(
            GroupWindowPowerSensor, "async_added_to_hass", restore_state_patch
        ):
            await sensor.async_added_to_hass()
            assert sensor.state == 99.9


@pytest.mark.asyncio
async def test_group_window_power_sensor_state_restoration_invalid_data(
    hass: HomeAssistant, mock_coordinator: AsyncMock
):
    """Test that GroupWindowPowerSensor handles invalid restored state data."""
    mock_coordinator.data = None  # No data from coordinator

    mock_device = Mock(spec=dr.DeviceEntry)
    mock_device.identifiers = {(DOMAIN, "group_test")}
    mock_device.name = "Test Group"
    mock_device.manufacturer = "Solar Window System"
    mock_device.model = "Group"

    sensor = GroupWindowPowerSensor(
        kind="group",
        object_name="Test Group",
        device=mock_device,
        key="total_power",
        label="Total Power",
        coordinator=mock_coordinator,
    )
    sensor.hass = hass

    # Mock async_get_last_state to return an invalid restored state
    with patch.object(
        sensor, "async_get_last_state", AsyncMock(return_value=Mock(state="invalid"))
    ):
        await sensor.async_added_to_hass()  # This calls async_get_last_state
        assert sensor.state is None  # Should return None if restored state is invalid


@pytest.mark.asyncio
async def test_group_window_power_sensor_friendly_name_update(
    hass: HomeAssistant, mock_coordinator: AsyncMock
):
    """Test that GroupWindowPowerSensor updates its friendly name in entity registry."""
    mock_device = Mock(spec=dr.DeviceEntry)
    mock_device.identifiers = {(DOMAIN, "group_test")}
    mock_device.name = "Test Group"
    mock_device.manufacturer = "Solar Window System"
    mock_device.model = "Group"

    sensor = GroupWindowPowerSensor(
        kind="group",
        object_name="Test Group",
        device=mock_device,
        key="total_power",
        label="Total Power",
        coordinator=mock_coordinator,
    )
    sensor.hass = hass
    sensor.entity_id = "sensor.sws_group_test_total_power"  # Manually set entity_id for registry lookup

    ent_reg = er.async_get(hass)
    # Register the config entry with hass
    config_entry = MockConfigEntry(domain=DOMAIN, entry_id="test_entry")
    config_entry.add_to_hass(hass)
    # Mock an existing entity entry with a different original name
    ent_reg.async_get_or_create(
        domain="sensor",
        platform=DOMAIN,
        unique_id=sensor.unique_id,
        suggested_object_id="sws_group_test_total_power",
        original_name="SWS_GROUP Test Group Total Power",  # This is the name before update
        config_entry=config_entry,
    )

    await sensor.async_added_to_hass()

    # Verify the name has been updated in the entity registry
    updated_entry = ent_reg.async_get(sensor.entity_id)
    assert updated_entry.name == "Total Power"


@pytest.mark.asyncio
async def test_group_window_power_sensor_attributes(
    hass: HomeAssistant, mock_coordinator: AsyncMock
):
    """Test that GroupWindowPowerSensor attributes are set correctly."""
    mock_device = Mock(spec=dr.DeviceEntry)
    mock_device.identifiers = {(DOMAIN, "group_test")}
    mock_device.name = "Test Group"
    mock_device.manufacturer = "Solar Window System"
    mock_device.model = "Group"

    sensor = GroupWindowPowerSensor(
        kind="group",
        object_name="Test Group",
        device=mock_device,
        key="total_power",
        label="Total Power",
        coordinator=mock_coordinator,
    )
    assert sensor.unit_of_measurement == "W"
    assert sensor.icon == "mdi:lightning-bolt"

    sensor_direct = GroupWindowPowerSensor(
        kind="group",
        object_name="Test Group",
        device=mock_device,
        key="total_power_direct",
        label="Total Power Direct",
        coordinator=mock_coordinator,
    )
    assert sensor_direct.icon == "mdi:weather-sunny"

    sensor_diffuse = GroupWindowPowerSensor(
        kind="group",
        object_name="Test Group",
        device=mock_device,
        key="total_power_diffuse",
        label="Total Power Diffuse",
        coordinator=mock_coordinator,
    )
    assert sensor_diffuse.icon == "mdi:weather-partly-cloudy"


@pytest.mark.asyncio
async def test_dummy_sensor_creation(hass: HomeAssistant):
    """Test that SolarWindowSystemGroupDummySensor is created correctly."""
    group_id = "test_group_id"
    group_name = "Test Group Name"
    sensor = SolarWindowSystemGroupDummySensor(group_id, group_name)

    assert sensor.name == f"Dummy Group Sensor ({group_name})"
    assert sensor.unique_id == f"{DOMAIN}_group_{group_id}_dummy"
    assert sensor.device_info["identifiers"] == {(DOMAIN, group_id)}
    assert sensor.device_info["name"] == group_name


@pytest.mark.asyncio
async def test_dummy_sensor_state_restoration(hass: HomeAssistant):
    """Test that SolarWindowSystemGroupDummySensor restores state or defaults."""
    group_id = "test_group_id"
    group_name = "Test Group Name"
    sensor = SolarWindowSystemGroupDummySensor(group_id, group_name)
    sensor.hass = hass

    # Test with restored state
    with patch.object(
        sensor, "async_get_last_state", AsyncMock(return_value=Mock(state="123"))
    ):
        await sensor.async_added_to_hass()
        assert sensor.state == 123

    # Test with invalid restored state
    sensor_invalid = SolarWindowSystemGroupDummySensor(group_id, group_name)
    sensor_invalid.hass = hass
    with patch.object(
        sensor_invalid,
        "async_get_last_state",
        AsyncMock(return_value=Mock(state="abc")),
    ):
        await sensor_invalid.async_added_to_hass()
        assert sensor_invalid.state == 42  # Should default to 42

    # Test with no restored state
    sensor_no_state = SolarWindowSystemGroupDummySensor(group_id, group_name)
    sensor_no_state.hass = hass
    with patch.object(
        sensor_no_state, "async_get_last_state", AsyncMock(return_value=None)
    ):
        await sensor_no_state.async_added_to_hass()
        assert sensor_no_state.state == 42  # Should default to 42
