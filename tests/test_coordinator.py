"""Tests for SolarCalculationCoordinator."""

import pytest
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator


@pytest.fixture
def mock_config():
    """Fixture for mock configuration."""
    return {
        "global": {
            "sensors": {
                "irradiance_sensor": "sensor.solar_irradiance",
                "temp_outdoor": "sensor.outdoor_temperature",
            },
            "thresholds": {
                "outside_temp": 25.0,
                "inside_temp": 24.0,
                "forecast_high": 28.0,
                "solar_energy": 300,
            },
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
def coordinator(hass, mock_config):
    """Fixture for SolarCalculationCoordinator instance."""
    from custom_components.solar_window_system.coordinator import SolarCalculationCoordinator
    return SolarCalculationCoordinator(hass, mock_config)


def test_coordinator_initialization(coordinator, mock_config):
    """Test coordinator initialization."""
    # Test coordinator is created
    assert coordinator is not None

    # Test DataUpdateCoordinator inheritance
    assert isinstance(coordinator, DataUpdateCoordinator)

    # Test config is stored
    assert coordinator.config == mock_config

    # Test windows are extracted
    expected_windows = {"test_window": mock_config["windows"]["test_window"]}
    assert coordinator.windows == expected_windows

    # Test groups are extracted
    assert coordinator.groups == mock_config.get("groups", {})

    # Test global_config is extracted
    assert coordinator.global_config == mock_config["global"]

    # Test sensors are extracted from global_config
    expected_sensors = mock_config["global"]["sensors"]
    assert coordinator.sensors == expected_sensors

    # Test thresholds are extracted from global_config
    expected_thresholds = mock_config["global"]["thresholds"]
    assert coordinator.thresholds == expected_thresholds


def test_sun_is_visible_above_horizon(coordinator, mock_config):
    """Test sun is visible when above horizon and within azimuth range."""
    window = mock_config["windows"]["test_window"]
    result = coordinator._sun_is_visible(
        elevation=45,
        azimuth=180,
        window=window
    )
    assert result is True


def test_sun_is_visible_below_horizon(coordinator, mock_config):
    """Test sun is not visible when below horizon."""
    window = mock_config["windows"]["test_window"]
    result = coordinator._sun_is_visible(
        elevation=-5,
        azimuth=180,
        window=window
    )
    assert result is False


def test_sun_is_visible_outside_azimuth_range(coordinator, mock_config):
    """Test sun is not visible when outside azimuth range."""
    window = mock_config["windows"]["test_window"]
    result = coordinator._sun_is_visible(
        elevation=45,
        azimuth=90,
        window=window
    )
    assert result is False


def test_sun_is_visible_blocked_by_shading(coordinator, mock_config):
    """Test sun is not visible when blocked by shading."""
    # Create a window with shading
    window_with_shading = {
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
            "window_recess": 30,
            "shading_depth": 100,
        },
    }
    result = coordinator._sun_is_visible(
        elevation=15,
        azimuth=180,
        window=window_with_shading
    )
    assert result is False
