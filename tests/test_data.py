"""Shared group and window options with numeric values for str conversion tests."""

VALID_GROUP_OPTIONS_NUMERIC = {
    "entry_type": "group",
    "name": "Test Group",
    "diffuse_factor": 0.15,
    "threshold_direct": 200,
    "threshold_diffuse": 150,
    "temperature_indoor_base": 23.0,
    "temperature_outdoor_base": 19.5,
    "indoor_temperature_sensor": "sensor.temp1",
}

VALID_WINDOW_OPTIONS_NUMERIC = {
    "entry_type": "window",
    "name": "Test Window",
    "g_value": 0.5,
    "frame_width": 0.125,
    "tilt": 90,
    "diffuse_factor": 0.15,
    "threshold_direct": 200,
    "threshold_diffuse": 150,
    "temperature_indoor_base": 23.0,
    "temperature_outdoor_base": 19.5,
    "indoor_temperature_sensor": "sensor.temp1",
}
# Shared group and window subentry mocks for entity tests
MOCK_GROUP_SUBENTRIES = {
    "group_id_1": {
        "subentry_type": "group",
        "title": "Living Room Group",
        "entry_id": "group_id_1",
    },
    "group_id_2": {
        "subentry_type": "group",
        "title": "Bedroom Group",
        "entry_id": "group_id_2",
    },
}

MOCK_WINDOW_SUBENTRIES = {
    "window_id_1": {
        "subentry_type": "window",
        "title": "Kitchen Window",
        "entry_id": "window_id_1",
    },
    "window_id_2": {
        "subentry_type": "window",
        "title": "Office Window",
        "entry_id": "window_id_2",
    },
}
# New: Shared window and group test data for calculator and flow tests
VALID_WINDOW_DATA = {
    "name": "South Window",
    "window_width": 2.0,
    "window_height": 1.5,
    "azimuth": 180,
    "elevation_min": 0,
    "elevation_max": 90,
    "azimuth_min": -90,
    "azimuth_max": 90,
    "shadow_depth": 0.5,
    "shadow_offset": 0.2,
    "indoor_temperature_sensor": "sensor.room_0_temp",
}

VALID_WINDOW_DATA_ALT = {
    "name": "North Window",
    "window_width": 1.0,
    "window_height": 1.0,
    "azimuth": 0,
    "elevation_min": 0,
    "elevation_max": 90,
    "azimuth_min": -45,
    "azimuth_max": 45,
    "shadow_depth": 0,
    "shadow_offset": 0,
    "indoor_temperature_sensor": "sensor.room_1_temp",
}

VALID_PHYSICAL = {
    "g_value": 0.7,
    "frame_width": 0.05,
    "diffuse_factor": 0.3,
    "tilt": 0,
}

VALID_THRESHOLDS = {"direct": 400, "diffuse": 200}
VALID_TEMPERATURES = {"indoor_base": 24, "outdoor_base": 25}
"""Central test data for Solar Window System tests."""

# Solar calculation test data
VALID_SOLAR_DATA = {
    "elevation": 45.0,
    "azimuth": 180.0,
    "radiation": 800.0,
    "diffuse_radiation": 200.0,
    "direct_radiation": 600.0,
}

VALID_SOLAR_DATA_LOW_ANGLE = {
    "elevation": 15.0,
    "azimuth": 180.0,
    "radiation": 300.0,
    "diffuse_radiation": 150.0,
    "direct_radiation": 150.0,
}

VALID_SOLAR_DATA_HIGH_ANGLE = {
    "elevation": 75.0,
    "azimuth": 180.0,
    "radiation": 950.0,
    "diffuse_radiation": 100.0,
    "direct_radiation": 850.0,
}

VALID_SOLAR_DATA_NIGHT = {
    "elevation": -5.0,
    "azimuth": 180.0,
    "radiation": 0.0,
    "diffuse_radiation": 0.0,
    "direct_radiation": 0.0,
}

# Window configuration test data for calculations
VALID_WINDOW_CALC_CONFIG = {
    "id": "test_window",
    "name": "Test Window",
    "area": 2.0,  # 2m²
    "azimuth": 180.0,  # South-facing
    "g_value": 0.8,
    "diffuse_factor": 0.3,
    "tilt": 90.0,  # Vertical window
    "shadow_depth": 0.5,
    "shadow_offset": 0.0,
    "thresholds": {
        "direct": 200.0,
        "diffuse": 100.0,
    },
}

VALID_WINDOW_CALC_CONFIG_WITH_SHADOW = {
    "id": "shadow_window",
    "name": "Shadow Window",
    "area": 3.0,
    "azimuth": 180.0,
    "g_value": 0.7,
    "diffuse_factor": 0.25,
    "tilt": 90.0,
    "shadow_depth": 1.0,
    "shadow_offset": 0.3,
    "thresholds": {
        "direct": 250.0,
        "diffuse": 120.0,
    },
}

# Entity states for solar sensors
VALID_SOLAR_ENTITY_STATES = {
    "sensor.solar_elevation": "45.0",
    "sensor.solar_azimuth": "180.0",
    "sensor.solar_radiation": "800.0",
    "sensor.diffuse_radiation": "200.0",
    "sensor.direct_radiation": "600.0",
    "sensor.outdoor_temperature": "25.0",
    "sensor.indoor_temperature": "22.0",
}

VALID_SOLAR_ENTITY_STATES_MISSING = {
    "sensor.solar_elevation": "unavailable",
    "sensor.solar_azimuth": None,
    "sensor.solar_radiation": "0.0",
    "sensor.outdoor_temperature": "20.0",
    "sensor.indoor_temperature": "21.0",
}

# Expected calculation results
EXPECTED_CALCULATION_RESULT_BASIC = {
    "power_total": 1280.0,  # 800 * 2.0 * 0.8 = 1280W
    "power_direct": 960.0,  # 600 * 2.0 * 0.8 = 960W
    "power_diffuse": 320.0,  # 200 * 2.0 * 0.8 * 0.3 = 320W (diffuse_factor applied)
    "power_direct_raw": 960.0,
    "power_diffuse_raw": 96.0,  # 200 * 2.0 * 0.8 * 0.3 = 96W (without diffuse_factor)
    "power_total_raw": 1056.0,  # 960 + 96
    "shadow_factor": 1.0,  # No shadow
    "is_visible": True,
    "area_m2": 2.0,
    "shade_required": True,  # Above threshold
    "shade_reason": "Direct radiation above threshold",
}

EXPECTED_CALCULATION_RESULT_WITH_SHADOW = {
    "power_total": 672.0,  # With shadow factor applied
    "power_direct": 336.0,  # 600 * 3.0 * 0.7 * 0.8 = 1008W * 0.8 shadow = 806.4W
    "power_diffuse": 157.5,  # 200 * 3.0 * 0.7 * 0.25 = 105W
    "shadow_factor": 0.8,  # Shadow applied
    "is_visible": True,
    "shade_required": True,
}

VALID_GLOBAL_BASIC = {
    "window_width": "1.5",
    "window_height": "2.0",
    "shadow_depth": "0.5",
    "shadow_offset": "0.2",
    "solar_radiation_sensor": "sensor.dummy_solar",
    "outdoor_temperature_sensor": "sensor.dummy_outdoor",
    "indoor_temperature_sensor": "sensor.dummy_indoor",
    "forecast_temperature_sensor": "sensor.dummy",
    "weather_warning_sensor": "binary_sensor.dummy",
}

VALID_GLOBAL_ENHANCED = {
    "g_value": "0.6",
    "frame_width": "0.1",
    "tilt": "90",
    "diffuse_factor": "0.2",
    "threshold_direct": "250",
    "threshold_diffuse": "120",
    "temperature_indoor_base": "22.0",
    "temperature_outdoor_base": "20.0",
}

VALID_GLOBAL_SCENARIOS = {
    "scenario_b_temp_indoor": "24",
    "scenario_b_temp_outdoor": "26",
    "scenario_c_temp_indoor": "22",
    "scenario_c_temp_outdoor": "25",
    "scenario_c_temp_forecast": "28",
    "scenario_c_start_hour": "8",
}

INVALID_GLOBAL_BASIC = {
    "window_width": "abc",
    "window_height": "2.0",
    "shadow_depth": "0.5",
    "shadow_offset": "0.2",
    "solar_radiation_sensor": "sensor.dummy_solar",
    "outdoor_temperature_sensor": "sensor.dummy_outdoor",
    "indoor_temperature_sensor": "sensor.dummy_indoor",
}
