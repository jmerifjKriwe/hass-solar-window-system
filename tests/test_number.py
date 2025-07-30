import pytest
from unittest.mock import MagicMock, call
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from custom_components.solar_window_system.number import (
    async_setup_entry,
    SolarGlobalSensitivityNumber,
    SolarChildrenFactorNumber,
    SolarTemperatureOffsetNumber,
    SolarGValueNumber,
    SolarFrameWidthNumber,
    SolarDiffuseFactorNumber,
    SolarTiltNumber,
    SolarThresholdDirectNumber,
    SolarThresholdDiffuseNumber,
    SolarTempIndoorBaseNumber,
    SolarTempOutdoorBaseNumber,
    SolarScenarioBTempIndoorOffsetNumber,
    SolarScenarioBTempOutdoorOffsetNumber,
    SolarScenarioCTempForecastThresholdNumber,
    SolarScenarioCStartHourNumber,
)


@pytest.fixture
def mock_entry():
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    # Simulate persistent options dict
    entry.options = {}
    return entry


@pytest.fixture
def mock_hass(mock_entry):
    hass = MagicMock(spec=HomeAssistant)

    # Patch config_entries.async_update_entry to update options dict
    def async_update_entry(entry, options=None):
        if options is not None:
            entry.options.update(options)

    hass.config_entries.async_update_entry.side_effect = async_update_entry
    return hass


def test_number_native_value_and_set(mock_hass, mock_entry):
    import asyncio

    # Global Sensitivity
    number = SolarGlobalSensitivityNumber(mock_hass, mock_entry)
    assert isinstance(number.native_value, float)
    asyncio.run(number.async_set_native_value(0.7))
    assert number.native_value == 0.7
    # Children Factor
    number = SolarChildrenFactorNumber(mock_hass, mock_entry)
    asyncio.run(number.async_set_native_value(1.2))
    assert number.native_value == 1.2
    # Temperature Offset
    number = SolarTemperatureOffsetNumber(mock_hass, mock_entry)
    asyncio.run(number.async_set_native_value(-2.0))
    assert number.native_value == -2.0


def test_number_default_values(mock_hass, mock_entry):
    # Global Sensitivity
    number = SolarGlobalSensitivityNumber(mock_hass, mock_entry)
    assert number.native_value == 1.0
    # Children Factor
    number = SolarChildrenFactorNumber(mock_hass, mock_entry)
    assert number.native_value == 0.8
    # Temperature Offset
    number = SolarTemperatureOffsetNumber(mock_hass, mock_entry)
    assert number.native_value == 0.0


def test_number_out_of_bounds(mock_hass, mock_entry):
    import asyncio

    number = SolarGlobalSensitivityNumber(mock_hass, mock_entry)

    # Test value below min
    asyncio.run(number.async_set_native_value(0.1))
    assert number.native_value == number.native_min_value

    # Test value above max
    asyncio.run(number.async_set_native_value(3.0))
    assert number.native_value == number.native_max_value


def test_async_setup_entry(mock_hass, mock_entry):
    import asyncio

    async_add_entities = MagicMock()
    asyncio.run(async_setup_entry(mock_hass, mock_entry, async_add_entities))
    async_add_entities.assert_called_once()
    
    # Check that all number entities are created
    assert len(async_add_entities.call_args[0][0]) == 15


@pytest.mark.parametrize(
    "number_class,expected_name,expected_unique_id,expected_icon,expected_min,expected_max,expected_step",
    [
        (SolarGlobalSensitivityNumber, "Global Sensitivity", "solar_window_system_global_sensitivity", "mdi:brightness-6", 0.5, 2.0, 0.1),
        (SolarChildrenFactorNumber, "Children Factor", "solar_window_system_children_factor", "mdi:human-child", 0.3, 1.5, 0.1),
        (SolarTemperatureOffsetNumber, "Temperature Offset", "solar_window_system_temperature_offset", "mdi:thermometer-plus", -5.0, 5.0, 0.5),
        (SolarGValueNumber, "G-Value (Energiedurchlassgrad)", "solar_window_system_g_value", "mdi:brightness-7", 0.1, 0.9, 0.01),
        (SolarFrameWidthNumber, "Frame Width", "solar_window_system_frame_width", "mdi:border-outside", 0.05, 0.3, 0.005),
        (SolarDiffuseFactorNumber, "Diffuse Factor", "solar_window_system_diffuse_factor", "mdi:weather-cloudy", 0.05, 0.5, 0.01),
        (SolarTiltNumber, "Window Tilt", "solar_window_system_tilt", "mdi:angle-acute", 0, 90, 1),
        (SolarThresholdDirectNumber, "Direct Radiation Threshold", "solar_window_system_threshold_direct", "mdi:weather-sunny", 50, 1000, 10),
        (SolarThresholdDiffuseNumber, "Diffuse Radiation Threshold", "solar_window_system_threshold_diffuse", "mdi:weather-partly-cloudy", 30, 800, 10),
        (SolarTempIndoorBaseNumber, "Base Indoor Temperature", "solar_window_system_temp_indoor_base", "mdi:home-thermometer", 18.0, 28.0, 0.5),
        (SolarTempOutdoorBaseNumber, "Base Outdoor Temperature", "solar_window_system_temp_outdoor_base", "mdi:thermometer", 15.0, 30.0, 0.5),
        (SolarScenarioBTempIndoorOffsetNumber, "Scenario B Indoor Temp Offset", "solar_window_system_scenario_b_temp_indoor_offset", "mdi:home-thermometer-outline", 0.0, 3.0, 0.1),
        (SolarScenarioBTempOutdoorOffsetNumber, "Scenario B Outdoor Temp Offset", "solar_window_system_scenario_b_temp_outdoor_offset", "mdi:thermometer-chevron-up", 3.0, 15.0, 0.5),
        (SolarScenarioCTempForecastThresholdNumber, "Scenario C Forecast Threshold", "solar_window_system_scenario_c_temp_forecast_threshold", "mdi:weather-sunny-alert", 25.0, 40.0, 0.5),
        (SolarScenarioCStartHourNumber, "Scenario C Start Hour", "solar_window_system_scenario_c_start_hour", "mdi:clock-time-nine", 6, 12, 1),
    ],
)
def test_entity_attributes(
    number_class,
    expected_name,
    expected_unique_id,
    expected_icon,
    expected_min,
    expected_max,
    expected_step,
    mock_hass,
    mock_entry,
):
    number = number_class(mock_hass, mock_entry)
    assert number.name == expected_name
    assert number.unique_id == expected_unique_id
    assert number.icon == expected_icon
    assert number.native_min_value == expected_min
    assert number.native_max_value == expected_max
    assert number.native_step == expected_step
