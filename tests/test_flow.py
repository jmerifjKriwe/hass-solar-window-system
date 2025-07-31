"""Test the config and options flow of the Solar Window System integration."""

import pytest
from unittest.mock import patch

from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN

MOCK_USER_INPUT = {
    "solar_radiation_sensor": "sensor.solar_radiation",
    "outdoor_temperature_sensor": "sensor.outdoor_temperature",
    "update_interval": 5,
    "min_solar_radiation": 50,
    "min_sun_elevation": 10,
}

MOCK_OPTIONS_INPUT = {
    "solar_radiation_sensor": "sensor.solar_radiation_new",
    "outdoor_temperature_sensor": "sensor.outdoor_temperature_new",
    "update_interval": 10,
    "min_solar_radiation": 60,
    "min_sun_elevation": 15,
    "weather_warning_sensor": "binary_sensor.weather_warning",
    "forecast_temperature_sensor": "sensor.forecast_temperature",
}


@pytest.mark.asyncio
async def test_full_config_flow_and_options_flow(hass: HomeAssistant):
    """Test the full config flow, from user setup to options update."""
    # -------------------------------------------------------------------
    # 1. Test Config Flow Initialization
    # -------------------------------------------------------------------
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"

    # -------------------------------------------------------------------
    # 2. Test Data Submission and Entry Creation
    # -------------------------------------------------------------------
    with patch(
        "custom_components.solar_window_system.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], MOCK_USER_INPUT
        )
        await hass.async_block_till_done()

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Solar Window System"
    assert result2["data"] == {}
    assert result2["options"] == MOCK_USER_INPUT
    assert len(mock_setup_entry.mock_calls) == 1

    # -------------------------------------------------------------------
    # 3. Test Options Flow Initialization
    # -------------------------------------------------------------------
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    result3 = await hass.config_entries.options.async_init(entry.entry_id)

    assert result3["type"] == data_entry_flow.FlowResultType.FORM
    assert result3["step_id"] == "init"

    # -------------------------------------------------------------------
    # 4. Test Options Flow Data Submission and Update
    # -------------------------------------------------------------------
    result4 = await hass.config_entries.options.async_configure(
        result3["flow_id"], user_input=MOCK_OPTIONS_INPUT
    )

    assert result4["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert entry.options == MOCK_OPTIONS_INPUT

    # -------------------------------------------------------------------
    # 5. Test Deletion of Optional Fields
    # -------------------------------------------------------------------
    result5 = await hass.config_entries.options.async_init(entry.entry_id)
    result6 = await hass.config_entries.options.async_configure(
        result5["flow_id"],
        user_input={
            **MOCK_OPTIONS_INPUT,
            "delete_weather_warning_sensor": True,
            "delete_forecast_temperature_sensor": True,
        },
    )
    assert result6["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert "weather_warning_sensor" not in entry.options
    assert "forecast_temperature_sensor" not in entry.options


@pytest.mark.asyncio
async def test_config_flow_already_configured(hass: HomeAssistant):
    """Test that the config flow aborts if the device is already configured."""
    MockConfigEntry(domain=DOMAIN).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "already_configured"
