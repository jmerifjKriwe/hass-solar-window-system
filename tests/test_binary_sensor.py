"""Unit tests for the binary_sensor entity."""
from unittest.mock import MagicMock

import pytest
from homeassistant.core import HomeAssistant

from custom_components.solar_window_system.binary_sensor import (
    SolarWindowShadingSensor,
    async_setup_entry,
)
from custom_components.solar_window_system.const import DOMAIN

from .conftest import setup_integration


@pytest.mark.asyncio
async def test_async_setup_entry(hass: HomeAssistant, setup_integration):
    """Test the binary sensor setup."""
    # This test ensures that the async_setup_entry function runs without errors
    # and that the entities are created.
    assert len(hass.states.async_entity_ids("binary_sensor")) > 0


def test_shading_sensor_properties():
    """Test the properties of the SolarWindowShadingSensor."""
    mock_coordinator = MagicMock()
    window_id = "test_window"
    mock_coordinator.data = {
        window_id: {
            "name": "Test Window",
            "shade_required": True,
            "shade_reason": "Strong sun",
            "power_total": 500,
            "effective_threshold": 400,
        }
    }

    sensor = SolarWindowShadingSensor(mock_coordinator, window_id)
    sensor.hass = MagicMock()
    sensor.entity_id = f"binary_sensor.{DOMAIN}_{window_id}_shading"

    assert sensor.is_on is True
    assert sensor.name == "Test Window Shading"
    assert sensor.unique_id == f"{DOMAIN}_{window_id}_shading"
    assert sensor.device_class == "opening"

    attributes = sensor.extra_state_attributes
    assert attributes["reason"] == "Strong sun"
    assert attributes["power_total_w"] == 500
    assert attributes["shading_threshold_w"] == 400


def test_shading_sensor_is_off():
    """Test the is_on property when shading is not required."""
    mock_coordinator = MagicMock()
    window_id = "test_window"
    mock_coordinator.data = {
        window_id: {
            "name": "Test Window",
            "shade_required": False,
        }
    }

    sensor = SolarWindowShadingSensor(mock_coordinator, window_id)
    assert sensor.is_on is False


def test_shading_sensor_no_coordinator_data():
    """Test the sensor when coordinator data is None."""
    mock_coordinator = MagicMock()
    mock_coordinator.data = None
    window_id = "test_window"

    sensor = SolarWindowShadingSensor(mock_coordinator, window_id)
    assert sensor.is_on is None
    assert sensor.extra_state_attributes == {}


async def test_async_setup_entry_no_data(hass: HomeAssistant, caplog):
    """Test async_setup_entry when coordinator data is None."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    coordinator = MagicMock()
    coordinator.data = None
    hass.data[DOMAIN] = {entry.entry_id: coordinator}
    async_add_entities = MagicMock()

    await async_setup_entry(hass, entry, async_add_entities)

    assert "Coordinator data is None" in caplog.text
    async_add_entities.assert_not_called()
