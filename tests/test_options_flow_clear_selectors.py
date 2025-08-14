"""
Tests for clearing selector fields in the options flow.

Ensures optional selectors can be cleared, are persisted as empty strings,
and reopen as empty in the first options step.
"""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN


@pytest.mark.skip(reason="Testen veraltete Logik und müssen noch auf den aktuellen Stand gebracht werden")
@pytest.mark.asyncio
async def test_clearing_selectors_persists_empty(
    hass: HomeAssistant, enable_custom_integrations: None
) -> None:
    """Clearing selector fields persists as empty and reopens empty."""
    # Create a config entry with selectors pre-set (options)
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Solar Window System",
        data={"entry_type": "global_config"},
        options={
            "forecast_temperature_sensor": "sensor.example_temp",
            "weather_warning_sensor": "binary_sensor.example_warn",
        },
    )
    entry.add_to_hass(hass)

    # Start Options Flow
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == "form"
    assert result["step_id"] == "global_basic"

    # Submit page 1 with cleared selectors (both empty)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "window_width": "1.0",
            "window_height": "1.0",
            "shadow_depth": "0.0",
            "shadow_offset": "0.0",
            "solar_radiation_sensor": "sensor.dummy_solar",
            "outdoor_temperature_sensor": "sensor.dummy_outdoor",
            "forecast_temperature_sensor": None,
            "weather_warning_sensor": None,
        },
    )
    assert result["type"] == "form"
    assert result["step_id"] == "global_enhanced"

    # Complete remaining pages with valid values
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "g_value": "0.5",
            "frame_width": "0.125",
            "tilt": "45",
            "diffuse_factor": "0.15",
            "threshold_direct": "200",
            "threshold_diffuse": "150",
            "temperature_indoor_base": "23.0",
            "temperature_outdoor_base": "19.5",
        },
    )
    assert result["type"] == "form"
    assert result["step_id"] == "global_scenarios"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "scenario_b_temp_indoor": "23.5",
            "scenario_b_temp_outdoor": "25.5",
            "scenario_c_temp_indoor": "21.5",
            "scenario_c_temp_outdoor": "24.0",
            "scenario_c_temp_forecast": "28.5",
            "scenario_c_start_hour": "9",
        },
    )
    assert result["type"] == "create_entry"

    # Ensure options were updated with cleared selections as empty strings
    entry = hass.config_entries.async_get_entry(entry.entry_id)
    assert entry is not None
    assert entry.options.get("forecast_temperature_sensor", "") == ""
    assert entry.options.get("weather_warning_sensor", "") == ""

    # Re-open Options Flow; defaults for selectors should be empty
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == "form"
    assert result["step_id"] == "global_basic"

    # Build schema defaults from result and verify selectors default to None/empty
    schema = result["data_schema"]
    defaults = {
        k: v.default() if hasattr(v, "default") else None
        for k, v in schema.schema.items()
    }
    # Optional keys exist in schema
    assert "forecast_temperature_sensor" in schema.schema
    assert "weather_warning_sensor" in schema.schema
    # Defaults for selectors should be None (rendered as empty)
    assert defaults.get("forecast_temperature_sensor") in (None, "")
    assert defaults.get("weather_warning_sensor") in (None, "")
