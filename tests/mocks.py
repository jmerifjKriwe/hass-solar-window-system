"""Mocks for solar_window_system integration tests."""

MOCK_GLOBAL_INPUT = {
    "solar_radiation_sensor": "sensor.mock_solar_radiation",
    "outdoor_temperature_sensor": "sensor.mock_outdoor_temperature",
    "update_interval": 5,
    "min_solar_radiation": 50.0,
    "min_sun_elevation": 10.0,
    "scenario_b_temp_indoor_threshold": 23.5,
    "scenario_b_temp_outdoor_threshold": 25.5,
    "scenario_c_temp_forecast_threshold": 28.5,
    "scenario_c_temp_indoor_threshold": 21.5,
    "scenario_c_temp_outdoor_threshold": 24.0,
    "scenario_c_start_hour": 9,
}

MOCK_WINDOW_INPUT = {
    "name": "Mock Window",
    "azimuth": 180.0,
    "width": 1.0,
    "height": 1.0,
    "room_temp_entity": "sensor.mock_room_temperature",
}

MOCK_GROUP_INPUT = {
    "name": "Mock Group",
    "windows": ["window.mock_window_1", "window.mock_window_2"],
}
