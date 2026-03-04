"""Tests for SolarEnergySensor entities."""

import pytest
from homeassistant.components.sensor import SensorEntity  # noqa: F401
from homeassistant.const import UnitOfPower
from homeassistant.helpers.entity import (
    DeviceInfo,
    Entity,  # noqa: F401
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator  # noqa: F401


@pytest.fixture
def mock_config():
    """Fixture for mock configuration."""
    return {
        "global": {
            "sensors": {
                "irradiance_sensor": "sensor.solar_irradiance",
            },
            "thresholds": {},
        },
        "windows": {
            "test_window": {
                "geometry": {
                    "width": 150,
                    "height": 120,
                    "azimuth": 180,
                    "tilt": 90,
                    "visible_azimuth_start": 150,
                    "visible_azimuth_end": 210,
                },
                "properties": {
                    "g_value": 0.6,
                    "frame_width": 10,
                    "window_recess": 0,
                    "shading_depth": 0,
                },
            },
        },
    }


@pytest.fixture
def mock_coordinator(hass, mock_config):
    """Fixture for mock coordinator with test data."""
    from custom_components.solar_window_system.coordinator import (
        SolarCalculationCoordinator,
    )

    coordinator = SolarCalculationCoordinator(hass, mock_config)

    # Set up mock data
    coordinator.data = {
        "test_window": {
            "direct": 500.0,
            "diffuse": 200.0,
            "combined": 700.0,
        },
        "group_test_group": {
            "direct": 1000.0,
            "diffuse": 400.0,
            "combined": 1400.0,
        },
        "global": {
            "direct": 2000.0,
            "diffuse": 800.0,
            "combined": 2800.0,
        },
    }

    return coordinator


def test_sensor_unique_id(mock_coordinator, mock_config):
    """Test sensor unique_id is generated correctly."""
    from custom_components.solar_window_system.const import (
        ENERGY_TYPE_DIRECT,
        LEVEL_WINDOW,
    )
    from custom_components.solar_window_system.sensor import SolarEnergySensor

    sensor = SolarEnergySensor(
        mock_coordinator, mock_config, LEVEL_WINDOW, "test_window", ENERGY_TYPE_DIRECT
    )

    assert sensor.unique_id == "solar_window_system_window_test_window_direct"


def test_sensor_name(mock_coordinator, mock_config):
    """Test sensor name contains window name and energy type."""
    from custom_components.solar_window_system.const import (
        ENERGY_TYPE_DIRECT,
        LEVEL_WINDOW,
    )
    from custom_components.solar_window_system.sensor import SolarEnergySensor

    sensor = SolarEnergySensor(
        mock_coordinator, mock_config, LEVEL_WINDOW, "test_window", ENERGY_TYPE_DIRECT
    )

    # Name should contain "Test Window", "Direct", and "Energy"
    name = sensor.name
    assert "Test Window" in name
    assert "Direct" in name
    assert "Energy" in name


def test_sensor_unit(mock_coordinator, mock_config):
    """Test sensor unit_of_measurement is WATT."""
    from custom_components.solar_window_system.const import (
        ENERGY_TYPE_DIRECT,
        LEVEL_WINDOW,
    )
    from custom_components.solar_window_system.sensor import SolarEnergySensor

    sensor = SolarEnergySensor(
        mock_coordinator, mock_config, LEVEL_WINDOW, "test_window", ENERGY_TYPE_DIRECT
    )

    assert sensor.unit_of_measurement == UnitOfPower.WATT


def test_sensor_device_class(mock_coordinator, mock_config):
    """Test sensor device_class is POWER."""
    from homeassistant.components.sensor import SensorDeviceClass

    from custom_components.solar_window_system.const import (
        ENERGY_TYPE_DIRECT,
        LEVEL_WINDOW,
    )
    from custom_components.solar_window_system.sensor import SolarEnergySensor

    sensor = SolarEnergySensor(
        mock_coordinator, mock_config, LEVEL_WINDOW, "test_window", ENERGY_TYPE_DIRECT
    )

    assert sensor.device_class == SensorDeviceClass.POWER


def test_sensor_state(mock_coordinator, mock_config):
    """Test sensor native_value returns correct energy value."""
    from custom_components.solar_window_system.const import (
        ENERGY_TYPE_DIRECT,
        LEVEL_WINDOW,
    )
    from custom_components.solar_window_system.sensor import SolarEnergySensor

    sensor = SolarEnergySensor(
        mock_coordinator, mock_config, LEVEL_WINDOW, "test_window", ENERGY_TYPE_DIRECT
    )

    # coordinator.data.test_window.direct = 500.0
    assert sensor.native_value == 500.0


def test_sensor_diffuse_type(mock_coordinator, mock_config):
    """Test sensor with ENERGY_TYPE_DIFFUSE returns diffuse value."""
    from custom_components.solar_window_system.const import (
        ENERGY_TYPE_DIFFUSE,
        LEVEL_WINDOW,
    )
    from custom_components.solar_window_system.sensor import SolarEnergySensor

    sensor = SolarEnergySensor(
        mock_coordinator, mock_config, LEVEL_WINDOW, "test_window", ENERGY_TYPE_DIFFUSE
    )

    # Should return diffuse value (200.0)
    assert sensor.native_value == 200.0


def test_sensor_combined_type(mock_coordinator, mock_config):
    """Test sensor with ENERGY_TYPE_COMBINED returns combined value."""
    from custom_components.solar_window_system.const import (
        ENERGY_TYPE_COMBINED,
        LEVEL_WINDOW,
    )
    from custom_components.solar_window_system.sensor import SolarEnergySensor

    sensor = SolarEnergySensor(
        mock_coordinator, mock_config, LEVEL_WINDOW, "test_window", ENERGY_TYPE_COMBINED
    )

    # Should return combined value (700.0)
    assert sensor.native_value == 700.0


def test_sensor_group_level(mock_coordinator, mock_config):
    """Test sensor at group level returns group data."""
    from custom_components.solar_window_system.const import (
        ENERGY_TYPE_DIRECT,
        LEVEL_GROUP,
    )
    from custom_components.solar_window_system.sensor import SolarEnergySensor

    sensor = SolarEnergySensor(
        mock_coordinator, mock_config, LEVEL_GROUP, "test_group", ENERGY_TYPE_DIRECT
    )

    # Should return group_test_group direct value (1000.0)
    assert sensor.native_value == 1000.0


def test_sensor_global_level(mock_coordinator, mock_config):
    """Test sensor at global level returns global data."""
    from custom_components.solar_window_system.const import (
        ENERGY_TYPE_COMBINED,
        LEVEL_GLOBAL,
    )
    from custom_components.solar_window_system.sensor import SolarEnergySensor

    sensor = SolarEnergySensor(
        mock_coordinator, mock_config, LEVEL_GLOBAL, "global", ENERGY_TYPE_COMBINED
    )

    # Should return global combined value (2800.0)
    assert sensor.native_value == 2800.0


def test_sensor_state_class(mock_coordinator, mock_config):
    """Test sensor has state_class 'measurement' for statistics."""
    from custom_components.solar_window_system.const import (
        ENERGY_TYPE_DIRECT,
        LEVEL_WINDOW,
    )
    from custom_components.solar_window_system.sensor import SolarEnergySensor

    sensor = SolarEnergySensor(
        mock_coordinator, mock_config, LEVEL_WINDOW, "test_window", ENERGY_TYPE_DIRECT
    )

    assert sensor.state_class == "measurement"


def test_sensor_device_info(mock_coordinator, mock_config):
    """Test sensor device_info returns DeviceInfo with identifiers."""
    from custom_components.solar_window_system.const import (
        DOMAIN,
        ENERGY_TYPE_DIRECT,
        LEVEL_WINDOW,
    )
    from custom_components.solar_window_system.sensor import SolarEnergySensor

    sensor = SolarEnergySensor(
        mock_coordinator, mock_config, LEVEL_WINDOW, "test_window", ENERGY_TYPE_DIRECT
    )

    device_info = sensor.device_info

    assert isinstance(device_info, DeviceInfo)
    assert device_info["identifiers"] == {(DOMAIN, "solar_window_system")}
