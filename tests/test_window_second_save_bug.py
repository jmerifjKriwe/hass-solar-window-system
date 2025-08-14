"""Test Window Options for the 'expected str' error on second save."""

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN


@pytest.mark.asyncio
async def test_window_options_second_save_expected_str_error(
    hass: HomeAssistant,
) -> None:
    """Test Window Options second save scenario for 'expected str' error."""
    print("🎯 Testing Window Options 'expected str' scenario...")

    # Step 1: Create initial window entry
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="test_window",
        data={
            "entry_type": "window",
            "name": "test_window",
        },
        options={},
        unique_id="test_window_second_save",
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Step 2: First save with numeric values
    print("📝 Step 2: First save with window numeric values...")
    flow_result1 = await hass.config_entries.options.async_init(config_entry.entry_id)

    first_save_input = {
        "name": "test_window",
        "indoor_temperature_sensor": "sensor.temp_room",
        "g_value": "0.6",
        "frame_width": "0.15",
        "tilt": "85",
        "diffuse_factor": "0.2",
        "threshold_direct": "250",
        "threshold_diffuse": "175",
        "temperature_indoor_base": "24.0",
        "temperature_outdoor_base": "18.5",
    }

    first_save_result = await hass.config_entries.options.async_configure(
        flow_result1["flow_id"], user_input=first_save_input
    )

    print(f"✅ First save result: {first_save_result['type']}")
    assert first_save_result["type"] == "create_entry"

    # Check stored values
    updated_entry = hass.config_entries.async_get_entry(config_entry.entry_id)
    print(f"📊 Stored options after first save: {updated_entry.options}")

    # Step 3: Second save - potential error scenario
    print("🔥 Step 3: Second save (Window Options problematic scenario)...")
    flow_result2 = await hass.config_entries.options.async_init(config_entry.entry_id)

    print(f"📋 Second flow schema type: {flow_result2['type']}")
    print(f"📋 Second flow step: {flow_result2['step_id']}")

    # Same values as before - this is where "expected str" might occur
    second_save_input = {
        "name": "test_window",
        "indoor_temperature_sensor": "sensor.temp_room",
        "g_value": "0.6",  # These might be the problem
        "frame_width": "0.15",  # if suggested_value is numeric
        "tilt": "85",
        "diffuse_factor": "0.2",
        "threshold_direct": "250",
        "threshold_diffuse": "175",
        "temperature_indoor_base": "24.0",
        "temperature_outdoor_base": "18.5",
    }

    try:
        second_save_result = await hass.config_entries.options.async_configure(
            flow_result2["flow_id"], user_input=second_save_input
        )
        print(f"✅ Second save result: {second_save_result['type']}")
        assert second_save_result["type"] == "create_entry"
        print("🎉 No Window Options error! The fix might be working.")

    except Exception as e:
        if "expected str" in str(e):
            print(f"🎯 FOUND THE WINDOW BUG! Error: {e}")
            pytest.fail(f"Found the 'expected str' error in Window Options: {e}")
        else:
            print(f"❌ Different error: {e}")
            raise
