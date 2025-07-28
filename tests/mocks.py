MOCK_CONFIG = {
    "defaults": {
        "physical": {
            "g_value": 0.5,
            "frame_width": 0.125,
            "diffuse_factor": 0.15,
            "tilt": 90,
        },
        "thresholds": {"direct": 200, "diffuse": 150},
        "temperatures": {"indoor_base": 23.0, "outdoor_base": 19.5},
        "scenario_b": {
            "enabled": True,
            "temp_indoor_offset": 0.5,
            "temp_outdoor_offset": 6.0,
        },
        "scenario_c": {
            "enabled": True,
            "temp_forecast_threshold": 28.5,
            "temp_indoor_threshold": 21.5,
            "temp_outdoor_threshold": 24.0,
            "start_hour": 9,
        },
        "calculation": {"min_solar_radiation": 50, "min_sun_elevation": 10},
    },
    "groups": {},
    "windows": {
        "test_window_south": {
            "name": "Test Window South",
            "room_temp_entity": "sensor.dummy_indoor_temp",
            "width": 2.0,
            "height": 2.0,
            "azimuth": 180,
            "azimuth_range": [-90, 90],
            "elevation_range": [0, 90],
        }
    },
}

MOCK_USER_INPUT = {
    "solar_radiation_sensor": "sensor.dummy_solar_radiation",
    "outdoor_temperature_sensor": "sensor.dummy_outdoor_temp",
}

MOCK_OPTIONS = {
    "global_sensitivity": 1.0,
    "children_factor": 1.0,
    "temperature_offset": 0.0,
    "scenario_b_enabled": True,
    "scenario_c_enabled": True,
    "debug_mode": False,
    "maintenance_mode": False,
}
