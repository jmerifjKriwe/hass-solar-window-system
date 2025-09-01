"""Tests for sensor platform."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import Mock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN
from custom_components.solar_window_system.sensor import (
    GroupWindowPowerSensor,
    SolarWindowSystemGroupDummySensor,
    async_setup_entry,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

# Test constants
EXPECTED_GROUP_SENSORS = 3
EXPECTED_WINDOW_SENSORS = 8
TEST_POWER_VALUE = 100
TEST_GROUP_POWER_VALUE = 200
DUMMY_SENSOR_VALUE = 42
TEST_RESTORED_STATE = 123.45


@pytest.mark.asyncio
async def test_async_setup_entry_global_config(hass: HomeAssistant) -> None:
    """Test async_setup_entry with global config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Solar Window System",
        data={},
        entry_id="global_entry",
    )

    # Mock device registry
    device = Mock()
    device.identifiers = {(DOMAIN, "global_config")}
    device.name = "Solar Window System"
    device.manufacturer = "Test Manufacturer"
    device.model = "Test Model"
    device.config_entries = {entry.entry_id}

    mock_device_registry = Mock()
    mock_device_registry.devices.values.return_value = [device]

    with patch(
        "homeassistant.helpers.device_registry.async_get",
        return_value=mock_device_registry,
    ):
        async_add_entities = Mock()
        await async_setup_entry(hass, entry, async_add_entities)

        # Should add global config sensor entities
        assert async_add_entities.call_count == 1
        entities = async_add_entities.call_args[0][0]
        assert len(entities) >= 1  # At least one sensor entity


@pytest.mark.asyncio
async def test_async_setup_entry_group_config(hass: HomeAssistant) -> None:
    """Test async_setup_entry with group config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Group Config",
        data={"entry_type": "group_configs"},
        entry_id="group_entry",
    )

    # Mock subentries
    subentry = Mock()
    subentry.subentry_type = "group"
    subentry.title = "Test Group"
    entry.subentries = {"group_1": subentry}

    # Mock device registry
    device = Mock()
    device.identifiers = {(DOMAIN, "group_group_1")}
    device.name = "Test Group"
    device.manufacturer = "Test Manufacturer"
    device.model = "Group"
    device.config_entries = {entry.entry_id}
    device.config_entries_subentries = {entry.entry_id: ["group_1"]}

    mock_device_registry = Mock()
    mock_device_registry.devices.values.return_value = [device]

    # Mock coordinator
    coordinator = Mock()
    coordinator.data = {
        "groups": {"group_1": {"name": "Test Group", "total_power": 100}}
    }

    with (
        patch(
            "homeassistant.helpers.device_registry.async_get",
            return_value=mock_device_registry,
        ),
        patch.dict(
            hass.data,
            {DOMAIN: {entry.entry_id: {"coordinator": coordinator}}},
        ),
    ):
        async_add_entities = Mock()
        await async_setup_entry(hass, entry, async_add_entities)

        # Should add group power sensor entities
        assert async_add_entities.call_count == 1
        entities = async_add_entities.call_args[0][0]
        assert len(entities) == EXPECTED_GROUP_SENSORS  # 3 power sensors for groups


@pytest.mark.asyncio
async def test_async_setup_entry_window_config(hass: HomeAssistant) -> None:
    """Test async_setup_entry with window config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Window Config",
        data={"entry_type": "window_configs"},
        entry_id="window_entry",
    )

    # Mock subentries
    subentry = Mock()
    subentry.subentry_type = "window"
    subentry.title = "Test Window"
    entry.subentries = {"window_1": subentry}

    # Mock device registry
    device = Mock()
    device.identifiers = {(DOMAIN, "window_window_1")}
    device.name = "Test Window"
    device.manufacturer = "Test Manufacturer"
    device.model = "Window"
    device.config_entries = {entry.entry_id}
    device.config_entries_subentries = {entry.entry_id: ["window_1"]}

    mock_device_registry = Mock()
    mock_device_registry.devices.values.return_value = [device]

    # Mock coordinator
    coordinator = Mock()
    coordinator.data = {
        "windows": {"window_1": {"name": "Test Window", "total_power": 50}}
    }

    with (
        patch(
            "homeassistant.helpers.device_registry.async_get",
            return_value=mock_device_registry,
        ),
        patch.dict(
            hass.data,
            {DOMAIN: {entry.entry_id: {"coordinator": coordinator}}},
        ),
    ):
        async_add_entities = Mock()
        await async_setup_entry(hass, entry, async_add_entities)

        # Should add window power sensor entities
        assert async_add_entities.call_count == 1
        entities = async_add_entities.call_args[0][0]
        assert len(entities) == EXPECTED_WINDOW_SENSORS  # 8 different power metrics
        # for windows


@pytest.mark.asyncio
async def test_async_setup_entry_no_global_device(hass: HomeAssistant) -> None:
    """Test async_setup_entry when no global device is found."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Solar Window System",
        data={},
        entry_id="global_entry",
    )

    # Mock empty device registry
    mock_device_registry = Mock()
    mock_device_registry.devices.values.return_value = []

    with patch(
        "homeassistant.helpers.device_registry.async_get",
        return_value=mock_device_registry,
    ):
        async_add_entities = Mock()
        await async_setup_entry(hass, entry, async_add_entities)

        # Should not add any entities when no global device found
        assert async_add_entities.call_count == 0


@pytest.mark.asyncio
async def test_async_setup_entry_group_no_subentries(hass: HomeAssistant) -> None:
    """Test async_setup_entry with group config but no subentries."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Group Config",
        data={"entry_type": "group_configs"},
        entry_id="group_entry",
    )

    entry.subentries = None

    with patch("homeassistant.helpers.device_registry.async_get"):
        async_add_entities = Mock()
        await async_setup_entry(hass, entry, async_add_entities)

        # Should not add any entities when no subentries
        assert async_add_entities.call_count == 0


@pytest.mark.asyncio
async def test_async_setup_entry_window_no_subentries(hass: HomeAssistant) -> None:
    """Test async_setup_entry with window config but no subentries."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Window Config",
        data={"entry_type": "window_configs"},
        entry_id="window_entry",
    )

    entry.subentries = None

    with patch("homeassistant.helpers.device_registry.async_get"):
        async_add_entities = Mock()
        await async_setup_entry(hass, entry, async_add_entities)

        # Should not add any entities when no subentries
        assert async_add_entities.call_count == 0


@pytest.mark.asyncio
async def test_group_window_power_sensor_window_data() -> None:
    """Test GroupWindowPowerSensor with window data."""
    device = Mock()
    device.identifiers = {(DOMAIN, "window_1")}
    device.name = "Test Window"
    device.manufacturer = "Test Manufacturer"
    device.model = "Window"

    coordinator = Mock()
    coordinator.data = {
        "windows": {
            "window_1": {
                "name": "Test Window",
                "total_power": 100,
                "total_power_direct": 80,
                "total_power_diffuse": 20,
            }
        }
    }

    sensor = GroupWindowPowerSensor(
        kind="window",
        object_name="Test Window",
        device=device,
        key_label=("total_power", "Total Power"),
        coordinator=coordinator,
    )

    # Test state property
    assert sensor.state == TEST_POWER_VALUE


@pytest.mark.asyncio
async def test_group_window_power_sensor_group_data() -> None:
    """Test GroupWindowPowerSensor with group data."""
    device = Mock()
    device.identifiers = {(DOMAIN, "group_1")}
    device.name = "Test Group"
    device.manufacturer = "Test Manufacturer"
    device.model = "Group"

    coordinator = Mock()
    coordinator.data = {
        "groups": {
            "group_1": {
                "name": "Test Group",
                "total_power": 200,
                "total_power_direct": 150,
                "total_power_diffuse": 50,
            }
        }
    }

    sensor = GroupWindowPowerSensor(
        kind="group",
        object_name="Test Group",
        device=device,
        key_label=("total_power", "Total Power"),
        coordinator=coordinator,
    )

    # Test state property
    assert sensor.state == TEST_GROUP_POWER_VALUE


@pytest.mark.asyncio
async def test_group_window_power_sensor_no_data() -> None:
    """Test GroupWindowPowerSensor when no coordinator data is available."""
    device = Mock()
    device.identifiers = {(DOMAIN, "window_1")}
    device.name = "Test Window"
    device.manufacturer = "Test Manufacturer"
    device.model = "Window"

    coordinator = Mock()
    coordinator.data = None

    sensor = GroupWindowPowerSensor(
        kind="window",
        object_name="Test Window",
        device=device,
        key_label=("total_power", "Total Power"),
        coordinator=coordinator,
    )

    # Test state property when no data
    assert sensor.state is None


@pytest.mark.asyncio
async def test_solar_window_system_group_dummy_sensor() -> None:
    """Test SolarWindowSystemGroupDummySensor."""
    sensor = SolarWindowSystemGroupDummySensor("group_1", "Test Group")

    # Test basic properties
    assert sensor.name == "Dummy Group Sensor (Test Group)"
    assert sensor.unique_id == "solar_window_system_group_group_1_dummy"
    assert sensor.state == DUMMY_SENSOR_VALUE


@pytest.mark.asyncio
async def test_group_window_power_sensor_async_added_to_hass() -> None:
    """Test GroupWindowPowerSensor async_added_to_hass method."""
    device = Mock()
    device.identifiers = {(DOMAIN, "window_1")}
    device.name = "Test Window"
    device.manufacturer = "Test Manufacturer"
    device.model = "Window"

    coordinator = Mock()
    coordinator.data = None

    sensor = GroupWindowPowerSensor(
        kind="window",
        object_name="Test Window",
        device=device,
        key_label=("total_power", "Total Power"),
        coordinator=coordinator,
    )

    # Mock entity registry
    mock_entity_registry = Mock()
    mock_entity_registry.entities = {}
    mock_entity_registry.async_update_entity = Mock()

    # Mock restored state
    restored_state = Mock()
    restored_state.state = "123.45"

    with (
        patch(
            "homeassistant.helpers.entity_registry.async_get",
            return_value=mock_entity_registry,
        ),
        patch.object(sensor, "async_get_last_state", return_value=restored_state),
    ):
        await sensor.async_added_to_hass()

        # Check that restored state was set
        assert sensor._restored_state == TEST_RESTORED_STATE  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_entity_creation_validation(hass: HomeAssistant) -> None:
    """Test that SWS sensor entities are properly created and registered."""
    # Test Global Configuration sensors
    global_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Solar Window System",
        data={},
        entry_id="global_entry",
    )

    # Mock device registry for global config
    global_device = Mock()
    global_device.identifiers = {(DOMAIN, "global_config")}
    global_device.name = "Solar Window System"
    global_device.manufacturer = "Test Manufacturer"
    global_device.model = "Test Model"
    global_device.config_entries = {global_entry.entry_id}

    mock_device_registry = Mock()
    mock_device_registry.devices.values.return_value = [global_device]

    # Mock entity registry to track created entities
    created_entities = []
    mock_entity_registry = Mock()

    with (
        patch(
            "homeassistant.helpers.device_registry.async_get",
            return_value=mock_device_registry,
        ),
        patch(
            "homeassistant.helpers.entity_registry.async_get",
            return_value=mock_entity_registry,
        ),
    ):
        async_add_entities = Mock(
            side_effect=lambda entities: created_entities.extend(entities)
        )
        await async_setup_entry(hass, global_entry, async_add_entities)

        # Verify global config entities were created
        assert len(created_entities) >= 1
        for entity in created_entities:
            assert hasattr(entity, "_attr_unique_id")
            assert hasattr(entity, "_attr_name")
            assert entity._attr_unique_id.startswith("sws_global_")


@pytest.mark.asyncio
async def test_group_window_entity_creation(hass: HomeAssistant) -> None:
    """Test that group and window power sensors are created with correct IDs."""
    # Test Group Configuration
    group_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Group Config",
        data={"entry_type": "group_configs"},
        entry_id="group_entry",
    )

    # Mock subentries
    group_subentry = Mock()
    group_subentry.subentry_type = "group"
    group_subentry.title = "Test Group"
    group_entry.subentries = {"group_1": group_subentry}

    # Mock device registry
    group_device = Mock()
    group_device.identifiers = {(DOMAIN, "group_group_1")}
    group_device.name = "Test Group"
    group_device.manufacturer = "Test Manufacturer"
    group_device.model = "Group"
    group_device.config_entries = {group_entry.entry_id}
    group_device.config_entries_subentries = {group_entry.entry_id: ["group_1"]}

    # Mock coordinator
    coordinator = Mock()
    coordinator.data = {
        "groups": {"group_1": {"name": "Test Group", "total_power": 100}}
    }

    created_group_entities = []

    with (
        patch(
            "homeassistant.helpers.device_registry.async_get",
            return_value=Mock(devices=Mock(values=Mock(return_value=[group_device]))),
        ),
        patch.dict(
            hass.data,
            {DOMAIN: {group_entry.entry_id: {"coordinator": coordinator}}},
        ),
    ):
        async_add_entities = Mock(
            side_effect=lambda entities, **_kwargs: (
                created_group_entities.extend(entities)
            )
        )
        await async_setup_entry(hass, group_entry, async_add_entities)

        # Verify group entities were created
        assert len(created_group_entities) == EXPECTED_GROUP_SENSORS

        # Check entity IDs and names
        expected_keys = ["total_power", "total_power_direct", "total_power_diffuse"]
        for i, entity in enumerate(created_group_entities):
            assert isinstance(entity, GroupWindowPowerSensor)
            assert entity._kind == "group"
            assert entity._object_name == "Test Group"
            assert entity._key == expected_keys[i]
            assert entity._attr_unique_id == f"sws_group_test_group_{expected_keys[i]}"
            assert "SWS_GROUP Test Group" in entity._attr_name


@pytest.mark.asyncio
async def test_window_entity_creation(hass: HomeAssistant) -> None:
    """Test that window power sensors are created with correct IDs and properties."""
    window_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Window Config",
        data={"entry_type": "window_configs"},
        entry_id="window_entry",
    )

    # Mock subentries
    window_subentry = Mock()
    window_subentry.subentry_type = "window"
    window_subentry.title = "Test Window"
    window_entry.subentries = {"window_1": window_subentry}

    # Mock device registry
    window_device = Mock()
    window_device.identifiers = {(DOMAIN, "window_window_1")}
    window_device.name = "Test Window"
    window_device.manufacturer = "Test Manufacturer"
    window_device.model = "Window"
    window_device.config_entries = {window_entry.entry_id}
    window_device.config_entries_subentries = {window_entry.entry_id: ["window_1"]}

    # Mock coordinator
    coordinator = Mock()
    coordinator.data = {
        "windows": {"window_1": {"name": "Test Window", "total_power": 50}}
    }

    created_window_entities = []

    with (
        patch(
            "homeassistant.helpers.device_registry.async_get",
            return_value=Mock(devices=Mock(values=Mock(return_value=[window_device]))),
        ),
        patch.dict(
            hass.data,
            {DOMAIN: {window_entry.entry_id: {"coordinator": coordinator}}},
        ),
    ):
        async_add_entities = Mock(
            side_effect=lambda entities, **_kwargs: (
                created_window_entities.extend(entities)
            )
        )
        await async_setup_entry(hass, window_entry, async_add_entities)

        # Verify window entities were created
        assert len(created_window_entities) == EXPECTED_WINDOW_SENSORS

        # Check entity properties
        expected_window_keys = [
            "total_power",
            "total_power_direct",
            "total_power_diffuse",
            "power_m2_total",
            "power_m2_diffuse",
            "power_m2_direct",
            "power_m2_raw",
            "total_power_raw",
        ]

        for i, entity in enumerate(created_window_entities):
            assert isinstance(entity, GroupWindowPowerSensor)
            assert entity._kind == "window"
            assert entity._object_name == "Test Window"
            assert entity._key == expected_window_keys[i]
            expected_id = f"sws_window_test_window_{expected_window_keys[i]}"
            assert entity._attr_unique_id == expected_id
            assert "SWS_WINDOW Test Window" in entity._attr_name
            assert entity._attr_unit_of_measurement == "W"


@pytest.mark.asyncio
async def test_entity_registry_integration(hass: HomeAssistant) -> None:
    """Test that entities are properly registered in HA entity registry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Solar Window System",
        data={},
        entry_id="test_entry",
    )

    # Mock device registry
    device = Mock()
    device.identifiers = {(DOMAIN, "global_config")}
    device.name = "Solar Window System"
    device.manufacturer = "Test Manufacturer"
    device.model = "Test Model"
    device.config_entries = {entry.entry_id}

    # Track entity registry calls
    registry_entities = {}
    registry_updates = []

    def mock_async_update_entity(entity_id: str, **kwargs: Any) -> None:
        registry_updates.append((entity_id, kwargs))

    mock_entity_registry = Mock()
    mock_entity_registry.entities = registry_entities
    mock_entity_registry.async_update_entity = mock_async_update_entity

    with (
        patch(
            "homeassistant.helpers.device_registry.async_get",
            return_value=Mock(devices=Mock(values=Mock(return_value=[device]))),
        ),
        patch(
            "homeassistant.helpers.entity_registry.async_get",
            return_value=mock_entity_registry,
        ),
    ):
        async_add_entities = Mock()
        await async_setup_entry(hass, entry, async_add_entities)

        # Verify entities were added
        assert async_add_entities.call_count == 1
        entities = async_add_entities.call_args[0][0]
        assert len(entities) >= 1

        # Check that entities have proper registry integration
        for entity in entities:
            assert hasattr(entity, "entity_id")
            assert hasattr(entity, "_attr_unique_id")
            assert entity._attr_unique_id.startswith("sws_global_")
