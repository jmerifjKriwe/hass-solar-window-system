"""Mocks for solar_window_system tests."""
from homeassistant.const import CONF_NAME

MOCK_USER_INPUT = {
    "solar_radiation_sensor": "sensor.dummy_solar_radiation",
    "outdoor_temperature_sensor": "sensor.dummy_outdoor_temp",
    "update_interval": 5,
    "min_solar_radiation": 50,
    "min_sun_elevation": 10,
    "weather_warning_sensor": "binary_sensor.dummy_weather_warning",
    "forecast_temperature_sensor": "sensor.dummy_forecast_temp",
}

MOCK_WINDOW_INPUT = {
    "type": "window",
    CONF_NAME: "Test Window South",
    "azimuth": 180,
    "width": 2,
    "height": 1.5,
    "tilt": 90,
    "g_value": 0.67,
    "frame_width": 0.1,
    "room_temp_entity": "sensor.dummy_indoor_temp",
}

MOCK_GROUP_INPUT = {
    "type": "group",
    CONF_NAME: "Test Group",
    "room_temp_entity": "sensor.dummy_indoor_temp_group",
}