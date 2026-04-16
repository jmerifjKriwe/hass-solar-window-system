"""Tests for debug sensors."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo

from custom_components.solar_window_system.const import (
    DEBUG_TYPE_CONFIG,
    DEBUG_TYPE_RUNTIME,
    DOMAIN,
)
from custom_components.solar_window_system.diagnostic_sensor import (
    ConfigDebugSensor,
    DebugSensorBase,
    RuntimeDebugSensor,
    async_setup_entry,
)


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator with error tracking."""
    coordinator = MagicMock()
    coordinator.data = {}
    coordinator.windows = {}
    coordinator.groups = {}
    return coordinator


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {}
    return hass


class TestDebugSensorBase:
    """Tests for DebugSensorBase class."""

    def test_get_error_count_text_ok(self, mock_coordinator):
        """Test error count text for zero errors."""
        sensor = DebugSensorBase(mock_coordinator, DEBUG_TYPE_CONFIG)
        assert sensor._get_error_count_text(0) == "OK"

    def test_get_error_count_text_single(self, mock_coordinator):
        """Test error count text for single error."""
        sensor = DebugSensorBase(mock_coordinator, DEBUG_TYPE_CONFIG)
        assert sensor._get_error_count_text(1) == "1 Fehler"

    def test_get_error_count_text_multiple(self, mock_coordinator):
        """Test error count text for multiple errors."""
        sensor = DebugSensorBase(mock_coordinator, DEBUG_TYPE_CONFIG)
        assert sensor._get_error_count_text(3) == "3 Fehler"

    def test_unique_id(self, mock_coordinator):
        """Test unique ID generation."""
        sensor = DebugSensorBase(mock_coordinator, DEBUG_TYPE_CONFIG)
        assert sensor.unique_id == f"{DOMAIN}_debug_config"

        sensor2 = DebugSensorBase(mock_coordinator, DEBUG_TYPE_RUNTIME)
        assert sensor2.unique_id == f"{DOMAIN}_debug_runtime"

    def test_entity_category(self, mock_coordinator):
        """Test entity category is diagnostic."""
        sensor = DebugSensorBase(mock_coordinator, DEBUG_TYPE_CONFIG)
        from homeassistant.const import EntityCategory

        assert sensor.entity_category == EntityCategory.DIAGNOSTIC


class TestConfigDebugSensor:
    """Tests for ConfigDebugSensor class."""

    def test_name(self, mock_coordinator):
        """Test sensor name."""
        sensor = ConfigDebugSensor(mock_coordinator)
        assert sensor.name == "Solar Window System Debug Config"

    def test_native_value_ok(self, mock_coordinator):
        """Test state when no config errors."""
        mock_coordinator.get_config_errors.return_value = []
        sensor = ConfigDebugSensor(mock_coordinator)
        assert sensor.native_value == "OK"

    def test_native_value_errors(self, mock_coordinator):
        """Test state when there are config errors."""
        mock_coordinator.get_config_errors.return_value = [
            "Fenster 'Wohnzimmer': Keine Azimuth",
            "Sensor 'x' nicht gefunden",
        ]
        sensor = ConfigDebugSensor(mock_coordinator)
        assert sensor.native_value == "2 Fehler"

    def test_extra_state_attributes_no_errors(self, mock_coordinator):
        """Test attributes when no errors."""
        mock_coordinator.get_config_errors.return_value = []
        sensor = ConfigDebugSensor(mock_coordinator)
        attrs = sensor.extra_state_attributes
        assert attrs["error_count"] == 0
        assert "errors" not in attrs
        assert "last_check" in attrs

    def test_extra_state_attributes_with_errors(self, mock_coordinator):
        """Test attributes when errors exist."""
        errors = ["Fenster 'A': Fehler 1", "Fenster 'B': Fehler 2"]
        mock_coordinator.get_config_errors.return_value = errors
        sensor = ConfigDebugSensor(mock_coordinator)
        attrs = sensor.extra_state_attributes
        assert attrs["error_count"] == 2
        assert attrs["errors"] == errors


class TestRuntimeDebugSensor:
    """Tests for RuntimeDebugSensor class."""

    def test_name(self, mock_coordinator):
        """Test sensor name."""
        sensor = RuntimeDebugSensor(mock_coordinator)
        assert sensor.name == "Solar Window System Debug Runtime"

    def test_native_value_ok(self, mock_coordinator):
        """Test state when no runtime errors."""
        mock_coordinator.get_runtime_errors.return_value = []
        sensor = RuntimeDebugSensor(mock_coordinator)
        assert sensor.native_value == "OK"

    def test_native_value_error(self, mock_coordinator):
        """Test state when there is a runtime error."""
        mock_coordinator.get_runtime_errors.return_value = ["Sensor unavailable"]
        sensor = RuntimeDebugSensor(mock_coordinator)
        assert sensor.native_value == "1 Fehler"

    def test_extra_state_attributes(self, mock_coordinator):
        """Test runtime sensor attributes."""
        mock_coordinator.get_runtime_errors.return_value = ["Error 1"]
        sensor = RuntimeDebugSensor(mock_coordinator)
        attrs = sensor.extra_state_attributes
        assert attrs["error_count"] == 1
        assert attrs["errors"] == ["Error 1"]
        assert "last_update" in attrs


@pytest.mark.asyncio
async def test_async_setup_entry(mock_hass, mock_coordinator):
    """Test that setup entry creates both debug sensors."""
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry"
    mock_hass.data[DOMAIN] = {mock_entry.entry_id: {"coordinator": mock_coordinator}}

    added_entities = []

    def mock_add_entities(entities):
        added_entities.extend(entities)

    await async_setup_entry(mock_hass, mock_entry, mock_add_entities)

    assert len(added_entities) == 2
    assert isinstance(added_entities[0], ConfigDebugSensor)
    assert isinstance(added_entities[1], RuntimeDebugSensor)


def test_diagnostic_sensor_in_platforms():
    """Test that diagnostic_sensor is included in PLATFORMS.

    This test would have caught the API mismatch error where
    diagnostic_sensor was loaded separately using the deprecated
    async_forward_entry_setup instead of async_forward_entry_setups.
    """
    from custom_components.solar_window_system import PLATFORMS

    assert "diagnostic_sensor" in PLATFORMS
    # Also verify all standard platforms are present
    from homeassistant.const import Platform

    assert Platform.SENSOR in PLATFORMS
    assert Platform.BINARY_SENSOR in PLATFORMS
