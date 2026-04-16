"""Tests for SolarCalculationCoordinator with subentries and overrides."""

from typing import cast

import pytest
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.solar_window_system.const import (
    CONF_GEOMETRY,
    CONF_GROUP_ID,
    CONF_HEIGHT,
    CONF_PROPERTIES,
    CONF_SENSORS,
    CONF_TEMP_INDOOR,
    CONF_TEMP_OUTDOOR,
    CONF_WIDTH,
    DEFAULT_G_VALUE,
    LEVEL_GROUP,
    LEVEL_WINDOW,
)
from custom_components.solar_window_system.coordinator import (
    SolarCalculationCoordinator,
)


@pytest.fixture
def mock_config():
    """Fixture for mock global configuration."""
    return {
        CONF_SENSORS: {
            "irradiance_sensor": "sensor.solar_irradiance",
            "temp_outdoor": "sensor.outdoor_temperature",
        },
        "properties": {
            "g_value": DEFAULT_G_VALUE,
        },
    }


@pytest.fixture
def mock_subentries():
    """Fixture for mock subentries (windows and groups)."""
    return {
        "test_window": {
            "type": "window",
            "name": "Test Window",
            CONF_GEOMETRY: {
                CONF_WIDTH: 150,
                CONF_HEIGHT: 120,
                "azimuth": 180,
                "tilt": 90,
                "visible_azimuth_start": 150,
                "visible_azimuth_end": 210,
            },
            CONF_PROPERTIES: {
                "g_value": 0.6,
                "frame_width": 10,
                "window_recess": 0,
                "shading_depth": 0,
            },
        },
    }


@pytest.fixture
def coordinator(hass, mock_config, mock_subentries) -> SolarCalculationCoordinator:
    """Fixture for SolarCalculationCoordinator instance with subentries."""
    return SolarCalculationCoordinator(hass, mock_config, mock_subentries, {})


async def test_coordinator_initialization(coordinator, mock_config, mock_subentries):
    """Test coordinator initialization with subentries."""
    # Cast to SolarCalculationCoordinator for type checking
    coord = cast(SolarCalculationCoordinator, coordinator)

    # Test coordinator is created
    assert coord is not None

    # Test DataUpdateCoordinator inheritance
    assert isinstance(coord, DataUpdateCoordinator)

    # Test config is stored
    assert coord.config == mock_config

    # Test windows are extracted from subentries
    assert "test_window" in coord.windows
    assert coord.windows["test_window"]["name"] == "Test Window"

    # Test groups are empty (no groups in mock_subentries)
    assert coord.groups == {}

    # Test global_sensors are extracted
    assert coord.global_sensors == mock_config[CONF_SENSORS]

    # Test global_properties are extracted
    assert coord.global_properties == mock_config["properties"]


async def test_sun_is_visible_above_horizon(coordinator, mock_subentries):
    """Test sun is visible when above horizon and within azimuth range."""
    coord = cast(SolarCalculationCoordinator, coordinator)
    result = coord._sun_is_visible(elevation=45, azimuth=180, window_id="test_window")
    assert result is True


async def test_sun_is_visible_below_horizon(coordinator):
    """Test sun is not visible when below horizon."""
    coord = cast(SolarCalculationCoordinator, coordinator)
    result = coord._sun_is_visible(elevation=-5, azimuth=180, window_id="test_window")
    assert result is False


async def test_sun_is_visible_outside_azimuth_range(coordinator):
    """Test sun is not visible when outside azimuth range."""
    coord = cast(SolarCalculationCoordinator, coordinator)
    result = coord._sun_is_visible(elevation=45, azimuth=90, window_id="test_window")
    assert result is False


async def test_sun_is_visible_blocked_by_shading(coordinator, hass, mock_config):
    """Test sun is not visible when blocked by shading."""
    # Create coordinator with window that has shading
    subentries_with_shading = {
        "window_with_shading": {
            "type": "window",
            "name": "Window with Shading",
            CONF_GEOMETRY: {
                CONF_WIDTH: 150,
                CONF_HEIGHT: 120,
                "azimuth": 180,
                "tilt": 90,
                "visible_azimuth_start": 150,
                "visible_azimuth_end": 210,
            },
            CONF_PROPERTIES: {
                "g_value": 0.6,
                "frame_width": 10,
                "window_recess": 30,
                "shading_depth": 100,
            },
        },
    }
    coordinator_shading = SolarCalculationCoordinator(
        hass, mock_config, subentries_with_shading, {}
    )

    # With shading_depth=100, window_recess=30:
    # Correct shade_angle = atan2(31, 100) = 17.22°
    # At elevation=15°, sun should be blocked
    result = coordinator_shading._sun_is_visible(
        elevation=15, azimuth=180, window_id="window_with_shading"
    )
    assert result is False


async def test_sun_is_visible_above_shading_angle(hass, mock_config):
    """Test sun is visible when above shading angle."""
    # Create coordinator with window that has shading
    subentries_with_shading = {
        "window_with_shading": {
            "type": "window",
            "name": "Window with Shading",
            CONF_GEOMETRY: {
                CONF_WIDTH: 150,
                CONF_HEIGHT: 120,
                "azimuth": 180,
                "tilt": 90,
                "visible_azimuth_start": 150,
                "visible_azimuth_end": 210,
            },
            CONF_PROPERTIES: {
                "g_value": 0.6,
                "frame_width": 10,
                "window_recess": 30,
                "shading_depth": 100,
            },
        },
    }
    coordinator_shading = SolarCalculationCoordinator(
        hass, mock_config, subentries_with_shading, {}
    )

    # At elevation=45°, sun should be visible (above the shading angle of ~17°)
    result = coordinator_shading._sun_is_visible(
        elevation=45, azimuth=180, window_id="window_with_shading"
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


async def test_estimate_diffuse_clear_sky(coordinator):
    """Test diffuse estimation for clear sky conditions."""
    # total=800, elevation=45, weather="sunny"
    result = coordinator._estimate_diffuse(
        irradiance_total=800, elevation=45, weather_condition="sunny"
    )

    # For sunny weather at 45° elevation:
    # Base ratio = 0.2 + (0.3 * (1 - 45/90)) = 0.2 + 0.15 = 0.35
    # Weather adjustment: "sunny" keeps base ratio
    # Expected: 800 * 0.35 = 280
    assert result == 280


async def test_estimate_diffuse_cloudy(coordinator):
    """Test diffuse estimation for cloudy conditions."""
    # total=400, elevation=30, weather="cloudy" → expect 300-350 (~80%)
    result = coordinator._estimate_diffuse(
        irradiance_total=400, elevation=30, weather_condition="cloudy"
    )

    # For cloudy weather, base_ratio should be 0.8
    # Expected: 400 * 0.8 = 320
    assert 300 <= result <= 350


async def test_estimate_diffuse_no_weather_condition(coordinator):
    """Test diffuse estimation with no weather condition."""
    # total=600, elevation=60, weather=None → expect 0 < result < total
    result = coordinator._estimate_diffuse(
        irradiance_total=600, elevation=60, weather_condition=None
    )

    # Should be between 0 and total
    assert 0 < result < 600


async def test_estimate_diffuse_low_sun(coordinator):
    """Test diffuse estimation for low sun angle."""
    # total=500, elevation=10, weather=None → expect result > total*0.4
    result = coordinator._estimate_diffuse(
        irradiance_total=500, elevation=10, weather_condition=None
    )

    # For low sun (10° elevation), base_ratio = 0.2 + (0.3 * (1 - 10/90)) = 0.2 + 0.267 = 0.467
    # Expected: 500 * 0.467 = 233.5, which is > 200 (total*0.4)
    assert result > 500 * 0.4


@pytest.mark.asyncio
async def test_async_update_returns_results(hass, coordinator):
    """Test _async_update returns results dict with window data."""
    # Set up sun state (above horizon)
    hass.states.async_set(
        "sun.sun",
        "above_horizon",
        {
            "elevation": 45,
            "azimuth": 180,
        },
    )

    # Set up irradiance sensor
    hass.states.async_set("sensor.solar_irradiance", "800")

    # Set up temperature sensor (not used but good to have)
    hass.states.async_set("sensor.outdoor_temperature", "28")

    # Call _async_update_data
    result = await coordinator._async_update_data()

    # Assert result is a dict with "test_window" key
    assert isinstance(result, dict)
    assert "test_window" in result


@pytest.mark.asyncio
async def test_async_update_night_returns_zero(hass, coordinator):
    """Test _async_update returns zero results when sun is below horizon."""
    # Set up sun state (below horizon - night)
    hass.states.async_set(
        "sun.sun",
        "below_horizon",
        {
            "elevation": -10,
            "azimuth": 180,
        },
    )

    # Set up sensors (should be ignored at night)
    hass.states.async_set("sensor.solar_irradiance", "800")
    hass.states.async_set("sensor.outdoor_temperature", "28")

    # Call _async_update_data
    result = await coordinator._async_update_data()

    # Assert all energies are 0
    assert "test_window" in result
    window_result = result["test_window"]
    assert window_result["direct"] == 0
    assert window_result["diffuse"] == 0
    assert window_result["combined"] == 0


@pytest.mark.asyncio
async def test_async_update_calculates_energy(hass, coordinator):
    """Test _async_update calculates energy correctly."""
    # Set up sun state (above horizon, south-facing)
    hass.states.async_set(
        "sun.sun",
        "above_horizon",
        {
            "elevation": 45,
            "azimuth": 180,  # South, matching window azimuth
        },
    )

    # Set up irradiance sensor
    hass.states.async_set("sensor.solar_irradiance", "800")

    # Call _async_update_data
    result = await coordinator._async_update_data()

    # Assert energy values are calculated
    assert "test_window" in result
    window_result = result["test_window"]

    # All values should be positive
    assert window_result["direct"] > 0
    assert window_result["diffuse"] > 0
    assert window_result["combined"] > 0

    # Combined should equal direct + diffuse
    assert window_result["combined"] == window_result["direct"] + window_result["diffuse"]


@pytest.mark.asyncio
async def test_aggregation_includes_groups(hass, mock_config):
    """Test that aggregation includes group results."""
    # Create coordinator with window and group
    subentries_with_group = {
        "test_window": {
            "type": "window",
            "name": "Test Window",
            CONF_GEOMETRY: {
                CONF_WIDTH: 150,
                CONF_HEIGHT: 120,
                "azimuth": 180,
                "tilt": 90,
                "visible_azimuth_start": 150,
                "visible_azimuth_end": 210,
            },
            CONF_PROPERTIES: {
                "g_value": 0.6,
                "frame_width": 10,
                "window_recess": 0,
                "shading_depth": 0,
            },
            CONF_GROUP_ID: "test_group",
        },
        "test_group": {
            "type": "group",
            "name": "Test Group",
            "windows": ["test_window"],
        },
    }
    coordinator = SolarCalculationCoordinator(hass, mock_config, subentries_with_group, {})

    # Set up sun state (above horizon)
    hass.states.async_set(
        "sun.sun",
        "above_horizon",
        {
            "elevation": 45,
            "azimuth": 180,
        },
    )

    # Set up irradiance sensor
    hass.states.async_set("sensor.solar_irradiance", "800")

    # Call _async_update_data
    result = await coordinator._async_update_data()

    # Assert group_test_group is in results
    assert "group_test_group" in result
    group_result = result["group_test_group"]
    assert "direct" in group_result
    assert "diffuse" in group_result
    assert "combined" in group_result


@pytest.mark.asyncio
async def test_aggregation_includes_global(hass, coordinator):
    """Test that aggregation includes global results."""
    # Set up sun state (above horizon)
    hass.states.async_set(
        "sun.sun",
        "above_horizon",
        {
            "elevation": 45,
            "azimuth": 180,
        },
    )

    # Set up irradiance sensor
    hass.states.async_set("sensor.solar_irradiance", "800")

    # Call _async_update_data
    result = await coordinator._async_update_data()

    # Assert global is in results
    assert "global" in result
    global_result = result["global"]
    assert "direct" in global_result
    assert "diffuse" in global_result
    assert "combined" in global_result

    # Global energy should be > 0 when sun is above horizon
    assert global_result["combined"] > 0


@pytest.mark.asyncio
async def test_aggregation_sums_correctly(hass):
    """Test that aggregation sums window values correctly."""
    # Create subentries with two windows and a group
    subentries_with_group = {
        "window_1": {
            "type": "window",
            "name": "Window 1",
            CONF_GEOMETRY: {
                CONF_WIDTH: 100,
                CONF_HEIGHT: 100,
                "azimuth": 180,
                "tilt": 90,
                "visible_azimuth_start": 150,
                "visible_azimuth_end": 210,
            },
            CONF_PROPERTIES: {
                "g_value": 0.6,
                "frame_width": 10,
                "window_recess": 0,
                "shading_depth": 0,
            },
        },
        "window_2": {
            "type": "window",
            "name": "Window 2",
            CONF_GEOMETRY: {
                CONF_WIDTH: 100,
                CONF_HEIGHT: 100,
                "azimuth": 180,
                "tilt": 90,
                "visible_azimuth_start": 150,
                "visible_azimuth_end": 210,
            },
            CONF_PROPERTIES: {
                "g_value": 0.6,
                "frame_width": 10,
                "window_recess": 0,
                "shading_depth": 0,
            },
        },
        "test_group": {
            "type": "group",
            "name": "Test Group",
            "windows": ["window_1", "window_2"],
        },
    }

    config = {
        CONF_SENSORS: {
            "irradiance_sensor": "sensor.solar_irradiance",
        },
    }

    coordinator = SolarCalculationCoordinator(hass, config, subentries_with_group, {})

    # Set up sun state (above horizon)
    hass.states.async_set(
        "sun.sun",
        "above_horizon",
        {
            "elevation": 45,
            "azimuth": 180,
        },
    )

    # Set up irradiance sensor
    hass.states.async_set("sensor.solar_irradiance", "800")

    # Call _async_update_data
    result = await coordinator._async_update_data()

    # Assert group sums windows correctly
    assert "group_test_group" in result
    group_result = result["group_test_group"]

    # Group direct should equal window_1 direct + window_2 direct
    expected_direct = result["window_1"]["direct"] + result["window_2"]["direct"]
    assert group_result["direct"] == expected_direct

    # Group diffuse should equal window_1 diffuse + window_2 diffuse
    expected_diffuse = result["window_1"]["diffuse"] + result["window_2"]["diffuse"]
    assert group_result["diffuse"] == expected_diffuse

    # Group combined should equal window_1 combined + window_2 combined
    expected_combined = result["window_1"]["combined"] + result["window_2"]["combined"]
    assert group_result["combined"] == expected_combined


# Tests for override functionality
@pytest.mark.asyncio
async def test_set_override(hass, mock_config, mock_subentries):
    """Test setting an override value."""
    coordinator = SolarCalculationCoordinator(hass, mock_config, mock_subentries, {})

    # Set an override for a threshold
    await coordinator.set_override(LEVEL_WINDOW, "test_window", "threshold_indoor", 26.0)

    # Check override is stored
    assert LEVEL_WINDOW in coordinator._overrides
    assert "test_window" in coordinator._overrides[LEVEL_WINDOW]
    assert coordinator._overrides[LEVEL_WINDOW]["test_window"]["threshold_indoor"] == 26.0


@pytest.mark.asyncio
async def test_get_effective_value_with_override(hass, mock_config, mock_subentries):
    """Test getting effective value with override set."""
    coordinator = SolarCalculationCoordinator(hass, mock_config, mock_subentries, {})

    # Set an override
    await coordinator.set_override(LEVEL_WINDOW, "test_window", "threshold_indoor", 26.0)

    # Get effective value should return override
    value = coordinator.get_effective_value(LEVEL_WINDOW, "test_window", "threshold_indoor")
    assert value == 26.0


@pytest.mark.asyncio
async def test_get_effective_value_without_override(hass, mock_config, mock_subentries):
    """Test getting effective value without override (returns default)."""
    coordinator = SolarCalculationCoordinator(hass, mock_config, mock_subentries, {})

    # Get effective value without override should return default
    value = coordinator.get_effective_value(LEVEL_WINDOW, "test_window", "threshold_indoor")
    assert value == 24.0  # DEFAULT_INSIDE_TEMP


@pytest.mark.asyncio
async def test_clear_overrides(hass, mock_config, mock_subentries):
    """Test clearing overrides."""
    coordinator = SolarCalculationCoordinator(hass, mock_config, mock_subentries, {})

    # Set an override
    await coordinator.set_override(LEVEL_WINDOW, "test_window", "threshold_indoor", 26.0)

    # Clear overrides
    await coordinator.clear_overrides(LEVEL_WINDOW, "test_window")

    # Check override is cleared
    assert "test_window" not in coordinator._overrides.get(LEVEL_WINDOW, {})


@pytest.mark.asyncio
async def test_subentries_extraction(hass, mock_config):
    """Test windows and groups extraction from subentries."""
    subentries = {
        "window_1": {"type": "window", "name": "Window 1"},
        "window_2": {"type": "window", "name": "Window 2"},
        "group_1": {"type": "group", "name": "Group 1", "windows": ["window_1"]},
        "other_key": {"type": "other", "name": "Other"},  # Should be ignored
    }

    coordinator = SolarCalculationCoordinator(hass, mock_config, subentries, {})

    # Only windows and groups should be extracted
    assert "window_1" in coordinator.windows
    assert "window_2" in coordinator.windows
    assert "group_1" in coordinator.groups
    assert "other_key" not in coordinator.windows
    assert "other_key" not in coordinator.groups
