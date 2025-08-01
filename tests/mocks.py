"""Mocks for solar_window_system tests."""
from homeassistant.const import CONF_NAME

from custom_components.solar_window_system.const import CONF_ENTRY_TYPE

MOCK_GLOBAL_INPUT = {
    CONF_ENTRY_TYPE: "global",
    "solar_radiation_sensor": "sensor.dummy_solar_radiation",
    "outdoor_temperature_sensor": "sensor.dummy_outdoor_temp",
    "update_interval": 5,
    "min_solar_radiation": 50,
    "min_sun_elevation": 10,
    "weather_warning_sensor": "binary_sensor.dummy_weather_warning",
    "forecast_temperature_sensor": "sensor.dummy_forecast_temp",
    "g_value": 0.5,
    "frame_width": 0.125,
    "tilt": 90,
    "diffuse_factor": 0.15,
    "threshold_direct": 200,
    "threshold_diffuse": 150,
    "indoor_base": 23.0,
    "outdoor_base": 19.5,
    "scenario_b_temp_indoor_threshold": 23.5,
    "scenario_b_temp_outdoor_threshold": 25.5,
    "scenario_c_temp_forecast_threshold": 28.5,
    "scenario_c_temp_indoor_threshold": 21.5,
    "scenario_c_temp_outdoor_threshold": 24.0,
    "scenario_c_start_hour": 9,
}

MOCK_WINDOW_INPUT = {
    CONF_ENTRY_TYPE: "window",
    CONF_NAME: "Test Window South",
    "azimuth": 180,
    "azimuth_range": [-90.0, 90.0],
    "elevation_range": [10.0, 90.0],
    "width": 2.0,
    "height": 1.5,
    "shadow_depth": 0.15,
    "shadow_offset": 0.0,
    "room_temp_entity": "sensor.dummy_indoor_temp",
    "tilt": 90,
    "g_value": 0.67,
    "frame_width": 0.1,
    "diffuse_factor": 0.15,
    "threshold_direct": 200,
    "threshold_diffuse": 150,
    "indoor_base": 23.0,
    "outdoor_base": 19.5,
    "scenario_b_temp_indoor_threshold": 23.5,
    "scenario_b_temp_outdoor_threshold": 25.5,
    "scenario_c_temp_forecast_threshold": 28.5,
    "scenario_c_temp_indoor_threshold": 21.5,
    "scenario_c_temp_outdoor_threshold": 24.0,
    "scenario_c_start_hour": 9,
}

MOCK_GROUP_INPUT = {
    CONF_ENTRY_TYPE: "group",
    CONF_NAME: "Test Group",
    "room_temp_entity": "sensor.dummy_indoor_temp_group",
}
