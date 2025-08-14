"""Test 'expected str' fix for all Options Flow scenarios."""

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_OK
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system import DOMAIN


@pytest.mark.asyncio
async def test_global_options_second_save_no_error(hass: HomeAssistant) -> None:
    """Test Global Options Flow second save works correctly."""
    # Create mock entry
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "entry_type": "global",
            "name": "test_global",
        },
        options={},
    )
    entry.add_to_hass(hass)

    # Setup entry
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state == ConfigEntryState.LOADED

    # Start options flow
    flows = hass.config_entries.options
    result = await flows.async_init(entry.entry_id)
    assert result["type"] == "form"
    assert result["step_id"] == "global_basic"

    # First save
    first_save = await flows.async_configure(
        result["flow_id"],
        {
            "window_width": "1.2",
            "window_height": "1.5",
            "shadow_depth": "0.3",
            "shadow_offset": "0.1",
            "solar_radiation_sensor": "sensor.solar",
            "outdoor_temperature_sensor": "sensor.temp_outdoor",
            "indoor_temperature_sensor": "sensor.temp_indoor",
        },
    )
    assert first_save["type"] == "form"
    assert first_save["step_id"] == "global_enhanced"

    # Continue to enhanced page
    enhanced_save = await flows.async_configure(
        first_save["flow_id"],
        {
            "g_value": "0.7",
            "frame_width": "0.12",
            "tilt": "75",
            "diffuse_factor": "0.25",
            "threshold_direct": "300",
            "threshold_diffuse": "200",
            "temperature_indoor_base": "22.5",
            "temperature_outdoor_base": "16.0",
        },
    )
    assert enhanced_save["type"] == "form"
    assert enhanced_save["step_id"] == "global_scenarios"

    # Complete scenarios page
    scenarios_result = await flows.async_configure(
        enhanced_save["flow_id"],
        {
            "scenario_b_temp_indoor": "25",
            "scenario_b_temp_outdoor": "20",
            "scenario_c_temp_indoor": "27",
            "scenario_c_temp_outdoor": "22",
            "scenario_c_temp_forecast": "24",
            "scenario_c_start_hour": "8",
        },
    )
    assert scenarios_result["type"] == "create_entry"

    # Verify options were saved
    stored_options = entry.options
    assert stored_options["window_width"] == "1.2"
    assert stored_options["g_value"] == "0.7"
    assert stored_options["tilt"] == "75"

    print("✅ Global Options first save completed successfully")

    # Start second options flow (this should work without errors)
    result2 = await flows.async_init(entry.entry_id)
    assert result2["type"] == "form"
    assert result2["step_id"] == "global_basic"

    # Second save without changes - this should not raise "expected str" error
    second_save = await flows.async_configure(
        result2["flow_id"],
        {
            "window_width": "1.2",  # Same values
            "window_height": "1.5",
            "shadow_depth": "0.3",
            "shadow_offset": "0.1",
            "solar_radiation_sensor": "sensor.solar",
            "outdoor_temperature_sensor": "sensor.temp_outdoor",
            "indoor_temperature_sensor": "sensor.temp_indoor",
        },
    )
    assert second_save["type"] == "form"
    assert second_save["step_id"] == "global_enhanced"

    print("🎉 Global Options second save works correctly!")


@pytest.mark.asyncio
async def test_group_options_second_save_no_error(hass: HomeAssistant) -> None:
    """Test Group Options Flow second save works correctly."""
    # Create global entry first
    global_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"entry_type": "global", "name": "test_global"},
        options={
            "g_value": "0.6",
            "frame_width": "0.15",
            "diffuse_factor": "0.2",
            "threshold_direct": "250",
            "threshold_diffuse": "175",
            "temperature_indoor_base": "24.0",
            "temperature_outdoor_base": "18.5",
        },
    )
    global_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(global_entry.entry_id)

    # Create group entry
    group_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"entry_type": "group", "name": "test_group"},
        options={},
    )
    group_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(group_entry.entry_id)

    # Start options flow
    flows = hass.config_entries.options
    result = await flows.async_init(group_entry.entry_id)
    assert result["type"] == "form"
    assert result["step_id"] == "group_options"

    # First save
    first_result = await flows.async_configure(
        result["flow_id"],
        {
            "name": "test_group",
            "indoor_temperature_sensor": "sensor.temp_room",
            "diffuse_factor": "0.3",
            "threshold_direct": "300",
        },
    )
    assert first_result["type"] == "create_entry"
    print("✅ Group Options first save completed successfully")

    # Start second options flow
    result2 = await flows.async_init(group_entry.entry_id)
    assert result2["type"] == "form"
    assert result2["step_id"] == "group_options"

    # Second save - this should not raise "expected str" error
    second_result = await flows.async_configure(
        result2["flow_id"],
        {
            "name": "test_group",
            "indoor_temperature_sensor": "sensor.temp_room",
            "diffuse_factor": "0.3",  # Same values
            "threshold_direct": "300",
        },
    )
    assert second_result["type"] == "create_entry"
    print("🎉 Group Options second save works correctly!")


@pytest.mark.asyncio
async def test_window_options_second_save_no_error(hass: HomeAssistant) -> None:
    """Test Window Options Flow second save works correctly."""
    # Create window entry
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"entry_type": "window", "name": "test_window"},
        options={},
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)

    # Start options flow
    flows = hass.config_entries.options
    result = await flows.async_init(entry.entry_id)
    assert result["type"] == "form"
    assert result["step_id"] == "window_options"

    # First save
    first_result = await flows.async_configure(
        result["flow_id"],
        {
            "name": "test_window",
            "indoor_temperature_sensor": "sensor.temp_room",
            "g_value": "0.6",
            "frame_width": "0.15",
            "tilt": "85",
            "diffuse_factor": "0.2",
            "temperature_indoor_base": "24.0",
            "temperature_outdoor_base": "18.5",
            "threshold_direct": "250",
            "threshold_diffuse": "175",
        },
    )
    assert first_result["type"] == "create_entry"
    print("✅ Window Options first save completed successfully")

    # Start second options flow
    result2 = await flows.async_init(entry.entry_id)
    assert result2["type"] == "form"
    assert result2["step_id"] == "window_options"

    # Second save - this should not raise "expected str" error
    second_result = await flows.async_configure(
        result2["flow_id"],
        {
            "name": "test_window",
            "indoor_temperature_sensor": "sensor.temp_room",
            "g_value": "0.6",  # Same numeric values
            "frame_width": "0.15",
            "tilt": "85",
            "diffuse_factor": "0.2",
            "temperature_indoor_base": "24.0",
            "temperature_outdoor_base": "18.5",
            "threshold_direct": "250",
            "threshold_diffuse": "175",
        },
    )
    assert second_result["type"] == "create_entry"
    print("🎉 Window Options second save works correctly!")
