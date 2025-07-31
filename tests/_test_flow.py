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

MOCK_THRESHOLDS_INPUT = {
    "diffuse_factor": 0.15,
    "threshold_direct": 200,
    "threshold_diffuse": 150,
    "indoor_base": 23.0,
    "outdoor_base": 19.5,
}

MOCK_SCENARIOS_INPUT = {
    "scenario_b_temp_indoor_offset": 0.5,
    "scenario_b_temp_outdoor_offset": 6.0,
    "scenario_c_temp_forecast_threshold": 28.5,
    "scenario_c_temp_indoor_threshold": 21.5,
    "scenario_c_temp_outdoor_threshold": 24.0,
    "scenario_c_start_hour": 9,
}


@pytest.mark.asyncio
async def test_full_config_flow_and_options_flow(hass: HomeAssistant):
    """Test the full config flow, from user setup to options update."""
    # 1. Test Config Flow Initialization
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"

    # 2. Test First Step (User)
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], MOCK_USER_INPUT
    )
    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["step_id"] == "thresholds"

    # 3. Test Second Step (Thresholds)
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"], MOCK_THRESHOLDS_INPUT
    )
    assert result3["type"] == data_entry_flow.FlowResultType.FORM
    assert result3["step_id"] == "scenarios"

    # 4. Test Third Step (Scenarios) and Entry Creation
    with patch(
        "custom_components.solar_window_system.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result4 = await hass.config_entries.flow.async_configure(
            result3["flow_id"], MOCK_SCENARIOS_INPUT
        )
        await hass.async_block_till_done()

    assert result4["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result4["title"] == "Solar Window System"
    assert result4["data"] == {}
    assert result4["options"] == {
        **MOCK_USER_INPUT,
        **MOCK_THRESHOLDS_INPUT,
        **MOCK_SCENARIOS_INPUT,
    }
    assert len(mock_setup_entry.mock_calls) == 1

    # 5. Test Options Flow
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    result5 = await hass.config_entries.options.async_init(entry.entry_id)
    assert result5["type"] == data_entry_flow.FlowResultType.FORM
    assert result5["step_id"] == "init"

    result6 = await hass.config_entries.options.async_configure(
        result5["flow_id"], user_input=MOCK_USER_INPUT
    )
    assert result6["type"] == data_entry_flow.FlowResultType.FORM
    assert result6["step_id"] == "thresholds"

    result7 = await hass.config_entries.options.async_configure(
        result6["flow_id"], user_input=MOCK_THRESHOLDS_INPUT
    )
    assert result7["type"] == data_entry_flow.FlowResultType.FORM
    assert result7["step_id"] == "scenarios"

    result8 = await hass.config_entries.options.async_configure(
        result7["flow_id"], user_input=MOCK_SCENARIOS_INPUT
    )
    assert result8["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert entry.options == {
        **MOCK_USER_INPUT,
        **MOCK_THRESHOLDS_INPUT,
        **MOCK_SCENARIOS_INPUT,
    }


@pytest.mark.asyncio
async def test_config_flow_already_configured(hass: HomeAssistant):
    """Test that the config flow aborts if the device is already configured."""
    MockConfigEntry(domain=DOMAIN).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "already_configured"