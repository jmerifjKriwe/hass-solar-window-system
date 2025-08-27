"""
Run SolarWindowCalculator with the user's sample data to ensure it executes.

This test reuses the flow-based calculator and monkeypatches entity state
accessors to provide the external sensor values the calculator expects.
"""

# ruff: noqa: S101,ANN001,ANN201

from unittest.mock import Mock

from custom_components.solar_window_system.calculator import SolarWindowCalculator
from homeassistant.config_entries import ConfigEntry


def test_calculator_with_user_sample(monkeypatch, hass):
    """Use the user's sample window/group/global data and mocked entities."""
    mock_entry = Mock(spec=ConfigEntry)
    mock_entry.data = {"entry_type": "window_configs"}

    calc = SolarWindowCalculator(hass, mock_entry)
    # Mark this calculator as flow-backed so it will perform window calculations
    calc.global_entry = mock_entry

    # Sample data adapted from the user's snippet (fixed key names)
    windows = {
        "og_kind2_ost": {
            "name": "OG Kind 2 - Ost",
            "azimuth": 118,
            "elevation_min": 20,
            "elevation_max": 90,
            "azimuth_min": -90,
            "azimuth_max": 90,
            "window_width": 1.17,
            "window_height": 1.25,
            "shadow_depth": -1,
            "shadow_offset": -1,
            "indoor_temperature_sensor": "-1",
            "linked_group_id": "group_kind2",
        }
    }

    groups = {
        "group_kind2": {
            "name": "Kind 2 Gruppe",
            "indoor_temperature_sensor": "sensor.temperatur_kind2",
            "scenario_c_enable": "enable",
            "diffuse_factor": -1,
            "threshold_direct": 100,
            "threshold_diffuse": 100,
            "temperature_indoor_base": 21.0,
            "temperature_outdoor_base": 19.5,
            "scenario_b_temp_indoor": 23.0,
            "scenario_b_temp_outdoor": 25.5,
            "scenario_c_temp_indoor": 28.5,
            "scenario_c_temp_outdoor": 21.5,
            "scenario_c_temp_forecast": 25.0,
            "scenario_c_start_hour": -1,
        }
    }

    global_data = {
        "solar_radiation_sensor": "sensor.solar_radiation",
        "outdoor_temperature_sensor": "sensor.outdoor_temp",
        "weather_forecast_temperature_sensor": "sensor.forecast_temp",
        "weather_warning_sensor": "binary_sensor.weather_warning",
        "scenario_b_enabled": True,
        "scenario_c_enabled": True,
        "maintenance_mode": False,
    }

    # Patch subentry lookup and global data merge
    monkeypatch.setattr(
        calc,
        "_get_subentries_by_type",
        lambda t: windows
        if t == "window"
        else (groups if t == "group" else {"global_config": global_data}),
    )
    monkeypatch.setattr(calc, "_get_global_data_merged", lambda: global_data)

    # Mock entity states accessed via _get_cached_entity_state
    def cached(entity_id, default=None, debug_label=None):
        mapping = {
            "sensor.temperatur_kind2": "25.29",
            "sensor.forecast_temp": "29.22",
            "sensor.solar_radiation": "342",
            "binary_sensor.weather_warning": "off",
            "sensor.outdoor_temp": "28.2",
        }
        return mapping.get(entity_id, default)

    monkeypatch.setattr(calc, "_get_cached_entity_state", cached)

    # Mock sun attributes
    def _get_safe_attr(*a, **kw):
        return 207.3 if a[1] == "azimuth" else 48.2

    monkeypatch.setattr(calc, "get_safe_attr", _get_safe_attr)

    # Inspect effective config used for this window
    effective_cfg, sources = calc.get_effective_config_from_flows("og_kind2_ost")
    # debug: effective_cfg logged during development

    # Execute calculation
    results = calc.calculate_all_windows_from_flows()
    # TEMP DEBUG: results available during development

    assert "og_kind2_ost" in results["windows"]
    win = results["windows"]["og_kind2_ost"]
    # Basic sanity checks
    assert "total_power" in win
    assert isinstance(win["total_power"], (int, float))

    # EXPECTATION: scenario C should trigger for these inputs and require shading
    assert "shade_required" in win
    assert win["shade_required"] is True
    # Reason should reference heatwave / forecast scenario
    assert "forecast" in (win.get("shade_reason") or "").lower()
