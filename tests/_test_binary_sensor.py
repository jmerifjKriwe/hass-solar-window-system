"""Unit tests for the binary_sensor entity."""
from unittest.mock import MagicMock

import logging
import copy
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from custom_components.solar_window_system import binary_sensor
from custom_components.solar_window_system.binary_sensor import (
    SolarWindowShadingSensor,
    async_setup_entry,
)
from custom_components.solar_window_system.const import DOMAIN


@pytest.fixture
def mock_coordinator():
    """Mock the data update coordinator."""
    coordinator = MagicMock()
    coordinator.data = copy.deepcopy({
        "window_1": {"name": "Living Room Window", "shade_required": True, "shade_reason": "Test", "power_total": 100, "effective_threshold": 50},
        "window_2": {"name": "Bedroom Window", "shade_required": False, "shade_reason": "Test", "power_total": 10, "effective_threshold": 50},
        "summary": {"total_power": 110},
    })
    return coordinator


@pytest.fixture
def mock_hass():
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {} # Initialize hass.data as a dictionary
    return hass


@pytest.mark.asyncio
async def test_async_setup_entry(hass: HomeAssistant, mock_coordinator):
    """Test the binary sensor setup creates the correct entities."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = mock_coordinator # Correctly set the coordinator

    async_add_entities = MagicMock()

    await async_setup_entry(hass, entry, async_add_entities)

    async_add_entities.assert_called_once()
    entities_added = async_add_entities.call_args[0][0]
    assert len(list(entities_added)) == 2
    unique_ids = {entity.unique_id for entity in entities_added}
    assert f"{DOMAIN}_window_1_shading" in unique_ids
    assert f"{DOMAIN}_window_2_shading" in unique_ids


def test_entity_attributes(mock_coordinator):
    """Test the attributes of the SolarWindowShadingSensor."""
    sensor = SolarWindowShadingSensor(mock_coordinator, "window_1")
    assert sensor.name == "Living Room Window Shading"
    assert sensor.unique_id == f"{DOMAIN}_window_1_shading"
    assert sensor.device_class == BinarySensorDeviceClass.OPENING
    assert sensor.is_on is True

    attributes = sensor.extra_state_attributes
    assert attributes["reason"] == "Test"
    assert attributes["power_total_w"] == 100
    assert attributes["shading_threshold_w"] == 50


def test_shading_sensor_is_off(mock_coordinator):
    """Test the is_on property when shading is not required."""
    sensor = SolarWindowShadingSensor(mock_coordinator, "window_2")
    assert sensor.is_on is False


def test_shading_sensor_no_coordinator_data():
    """Test the sensor when coordinator data is None."""
    mock_coord = MagicMock()
    mock_coord.data = None
    sensor = SolarWindowShadingSensor(mock_coord, "test_window")
    assert sensor.is_on is None
    assert sensor.extra_state_attributes == {}


@pytest.mark.asyncio
async def test_async_setup_entry_no_data(hass: HomeAssistant, caplog):
    """Test async_setup_entry when coordinator data is None."""
    with caplog.at_level(logging.INFO, logger=binary_sensor._LOGGER.name):
        entry = MagicMock()
        entry.entry_id = "test_entry_id"
        coordinator = MagicMock()
        coordinator.data = None
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator # Correctly set the coordinator
        async_add_entities = MagicMock()

        await async_setup_entry(hass, entry, async_add_entities)

        assert "Coordinator data is None" in caplog.text
        async_add_entities.assert_not_called()


@pytest.mark.parametrize(
    "missing_key,expected_is_on,expected_attrs",
    [
        ("shade_required", None, {"reason": "Test", "power_total_w": 100, "shading_threshold_w": 50}),
        ("shade_reason", True, {"reason": None, "power_total_w": 100, "shading_threshold_w": 50}),
        ("power_total", True, {"reason": "Test", "power_total_w": 0, "shading_threshold_w": 50}),
        ("effective_threshold", True, {"reason": "Test", "power_total_w": 100, "shading_threshold_w": 0}),
    ],
)
def test_shading_sensor_missing_keys(mock_coordinator, missing_key, expected_is_on, expected_attrs):
    del mock_coordinator.data["window_1"][missing_key]
    sensor = SolarWindowShadingSensor(mock_coordinator, "window_1")
    assert sensor.is_on == expected_is_on
    assert sensor.extra_state_attributes == expected_attrs


@pytest.mark.parametrize(
    "key,wrong_value,expected_is_on,expected_attrs",
    [
        ("shade_required", "not_a_bool", None, {"reason": "Test", "power_total_w": 100, "shading_threshold_w": 50}),
        ("shade_reason", 123, True, {"reason": 123, "power_total_w": 100, "shading_threshold_w": 50}),
        ("power_total", "not_a_number", True, {"reason": "Test", "power_total_w": 0, "shading_threshold_w": 50}),
        ("effective_threshold", "not_a_number", True, {"reason": "Test", "power_total_w": 100, "shading_threshold_w": 0}),
    ],
)
def test_shading_sensor_wrong_data_types(mock_coordinator, key, wrong_value, expected_is_on, expected_attrs):
    mock_coordinator.data["window_1"][key] = wrong_value
    sensor = SolarWindowShadingSensor(mock_coordinator, "window_1")
    assert sensor.is_on == expected_is_on
    assert sensor.extra_state_attributes == expected_attrs
