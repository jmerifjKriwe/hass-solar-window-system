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
    # With shading_depth=100, window_recess=30:
    # Correct shade_angle = atan2(31, 100) = 17.22°
    # At elevation=15°, sun should be blocked
    result = coordinator._sun_is_visible(
        elevation=15,
        azimuth=180,
        window=window_with_shading
    )
    assert result is False


def test_sun_is_visible_above_shading_angle(coordinator, mock_config):
    """Test sun is visible when above shading angle.

    This test would catch the atan2 parameter swap bug:
    - With CORRECT formula: shade_angle = atan2(31, 100) = 17.22°
      At elevation=45°, sun should be visible (45 > 17.22)
    - With WRONG formula: shade_angle = atan2(100, 31) = 72.78°
      At elevation=45°, sun would be blocked (45 < 72.78)
    """
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
    # At elevation=45°, sun should be visible (above the shading angle of ~17°)
    result = coordinator._sun_is_visible(
        elevation=45,
        azimuth=180,
        window=window_with_shading
    )
    assert result is True


@pytest.mark.asyncio
async def test_safe_get_sensor_valid(hass, coordinator):
    """Test _safe_get_sensor with valid numeric state."""
    # Set up a sensor with a valid numeric state
    hass.states.async_set("sensor.test_temp", "25.5")

    # Call the method
    result = await coordinator._safe_get_sensor("sensor.test_temp")

    # Assert it returns the float value
    assert result == 25.5


@pytest.mark.asyncio
async def test_safe_get_sensor_unknown(hass, coordinator):
    """Test _safe_get_sensor with 'unknown' state."""
    # Set up a sensor with 'unknown' state
    hass.states.async_set("sensor.test_temp", "unknown")

    # Call the method
    result = await coordinator._safe_get_sensor("sensor.test_temp")

    # Assert it returns None for unknown state
    assert result is None


@pytest.mark.asyncio
async def test_safe_get_sensor_unavailable(hass, coordinator):
    """Test _safe_get_sensor with 'unavailable' state."""
    # Set up a sensor with 'unavailable' state
    hass.states.async_set("sensor.test_temp", "unavailable")

    # Call the method
    result = await coordinator._safe_get_sensor("sensor.test_temp")

    # Assert it returns None for unavailable state
    assert result is None


@pytest.mark.asyncio
async def test_safe_get_sensor_missing(hass, coordinator):
    """Test _safe_get_sensor with non-existent sensor."""
    # Don't create the sensor - it should be missing

    # Call the method
    result = await coordinator._safe_get_sensor("sensor.nonexistent")

    # Assert it returns None for missing sensor
    assert result is None


@pytest.mark.asyncio
async def test_safe_get_sensor_with_default(hass, coordinator):
    """Test _safe_get_sensor with default value."""
    # Set up a sensor with 'unknown' state
    hass.states.async_set("sensor.test_temp", "unknown")

    # Call the method with a default value
    result = await coordinator._safe_get_sensor("sensor.test_temp", default=20.0)

    # Assert it returns the default value
    assert result == 20.0


def test_estimate_diffuse_clear_sky(coordinator):
    """Test diffuse estimation for clear sky conditions."""
    # total=800, elevation=45, weather="sunny"
    result = coordinator._estimate_diffuse(
        irradiance_total=800,
        elevation=45,
        weather_condition="sunny"
    )

    # For sunny weather at 45° elevation:
    # Base ratio = 0.2 + (0.3 * (1 - 45/90)) = 0.2 + 0.15 = 0.35
    # Weather adjustment: "sunny" keeps base ratio
    # Expected: 800 * 0.35 = 280
    assert result == 280


def test_estimate_diffuse_cloudy(coordinator):
    """Test diffuse estimation for cloudy conditions."""
    # total=400, elevation=30, weather="cloudy" → expect 300-350 (~80%)
    result = coordinator._estimate_diffuse(
        irradiance_total=400,
        elevation=30,
        weather_condition="cloudy"
    )

    # For cloudy weather, base_ratio should be 0.8
    # Expected: 400 * 0.8 = 320
    assert 300 <= result <= 350


def test_estimate_diffuse_no_weather_condition(coordinator):
    """Test diffuse estimation with no weather condition."""
    # total=600, elevation=60, weather=None → expect 0 < result < total
    result = coordinator._estimate_diffuse(
        irradiance_total=600,
        elevation=60,
        weather_condition=None
    )

    # Should be between 0 and total
    assert 0 < result < 600


def test_estimate_diffuse_low_sun(coordinator):
    """Test diffuse estimation for low sun angle."""
    # total=500, elevation=10, weather=None → expect result > total*0.4
    result = coordinator._estimate_diffuse(
        irradiance_total=500,
        elevation=10,
        weather_condition=None
    )

    # For low sun (10° elevation), base_ratio = 0.2 + (0.3 * (1 - 10/90)) = 0.2 + 0.267 = 0.467
    # Expected: 500 * 0.467 = 233.5, which is > 200 (total*0.4)
    assert result > 500 * 0.4
