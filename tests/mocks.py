# tests/mocks.py

"""Mock data for tests."""

MOCK_CONFIG = {
    "groups": {
        "group_with_override": {"thresholds": {"direct": 100}},
        "children": {},  # Gruppe für den children_factor Test
    },
    "windows": {
        "test_window_south": {
            "name": "Test Window South",
            "room_temp_entity": "sensor.dummy_indoor_temp",
            "width": 2.0,
            "height": 2.0,
            "azimuth": 180,
            "azimuth_range": [-90, 90],
            "elevation_range": [0, 90],
            "group_type": "default",
        },
        "test_window_group": {
            "name": "Test Window Group Override",
            "room_temp_entity": "sensor.dummy_indoor_temp_group",
            "width": 1.0,
            "height": 1.0,
            "azimuth": 180,
            "azimuth_range": [-90, 90],
            "elevation_range": [0, 90],
            "group_type": "group_with_override",
        },
        "test_window_direct": {
            "name": "Test Window Direct Override",
            "room_temp_entity": "sensor.dummy_indoor_temp_direct",
            "width": 1.0,
            "height": 1.0,
            "azimuth": 180,
            "azimuth_range": [-90, 90],
            "elevation_range": [0, 90],
            "group_type": "default",
            "overrides": {"thresholds": {"direct": 120}},
        },
        "test_window_children": {
            "name": "Test Window Children",
            "room_temp_entity": "sensor.dummy_indoor_temp_children",
            "width": 1.5,
            "height": 1.5,
            "azimuth": 180,
            "azimuth_range": [-90, 90],
            "elevation_range": [0, 90],
            "group_type": "children",
        },
        "test_window_bad_group": {
            "name": "Test Window Bad Group",
            "room_temp_entity": "sensor.dummy_indoor_temp_bad_group",
            "width": 1.0,
            "height": 1.0,
            "azimuth": 180,  # KORREKTUR: Von 90 auf 180 geändert, um die Sonne direkt zu sehen
            "azimuth_range": [-90, 90],
            "elevation_range": [0, 90],
            "group_type": "non_existent_group",  # Diese Gruppe gibt es nicht
        },
    },
}

MOCK_USER_INPUT = {
    "solar_radiation_sensor": "sensor.dummy_solar_radiation",
    "outdoor_temperature_sensor": "sensor.dummy_outdoor_temp",
    "forecast_temperature_sensor": "sensor.dummy_forecast_temp",
}

MOCK_OPTIONS = {
    "update_interval": 5,
    "global_sensitivity": 1.0,
    "children_factor": 1.0,
    "temperature_offset": 0.0,
    "scenario_b_enabled": True,
    "scenario_c_enabled": True,
    "debug_mode": False,
    "maintenance_mode": False,
}
