"""Tests for SolarCalculationCoordinator."""

import pytest
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator


@pytest.fixture
def mock_config():
    """Fixture for mock configuration."""
    return {
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
        "windows": {
            "test_window": {
                "geometry": {
                    "width": 150,
                    "height": 120,
                    "azimuth": 180,
                    "tilt": 90,
                    "azimuth_start": 150,
                    "azimuth_end": 210,
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

    # Test config is stored
    assert coordinator.config == mock_config

    # Test windows are extracted
    expected_windows = {"test_window": mock_config["windows"]["test_window"]}
    assert coordinator.windows == expected_windows
