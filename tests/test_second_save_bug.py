"""Test to reproduce the exact 'expected str' error scenario."""

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN


@pytest.mark.asyncio
async def test_group_options_second_save_expected_str_error(
    hass: HomeAssistant,
) -> None:
    """
    Test the exact scenario described:
    1. Create group entry
    2. Save options once (this works)
    3. Open options flow again
    4. Save again without changes (this should fail with 'expected str')
    """
    print("🎯 Testing the exact 'expected str' scenario...")

    # Step 1: Create initial group entry
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="testgruppe21",
        data={
            "entry_type": "group",
            "name": "testgruppe21",
            # Start with no numeric values - just like when first created
        },
        options={},
        unique_id="test_group_second_save",
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # Step 2: First save - add some numeric values (this should work)
    print("📝 Step 2: First save with numeric values...")
    flow_result1 = await hass.config_entries.options.async_init(config_entry.entry_id)

    first_save_input = {
        "name": "testgruppe21",
        "indoor_temperature_sensor": "sensor.temp_kitchen",
        "diffuse_factor": "-1",  # Sentinel value as string
        "threshold_direct": "-1",  # Sentinel value as string
        "threshold_diffuse": "500",  # Real value as string
        "temperature_indoor_base": "-1",  # Sentinel value as string
        "temperature_outdoor_base": "-1",  # Sentinel value as string
    }

    first_save_result = await hass.config_entries.options.async_configure(
        flow_result1["flow_id"], user_input=first_save_input
    )

    print(f"✅ First save result: {first_save_result['type']}")
    assert first_save_result["type"] == "create_entry"

    # Check that the values are now stored as numbers in the config entry
    updated_entry = hass.config_entries.async_get_entry(config_entry.entry_id)
    print(f"📊 Stored options after first save: {updated_entry.options}")

    # Step 3: Second save - this is where the error should occur
    print("🔥 Step 3: Second save (the problematic scenario)...")
    flow_result2 = await hass.config_entries.options.async_init(config_entry.entry_id)

    print(f"📋 Second flow schema type: {flow_result2['type']}")
    print(f"📋 Second flow step: {flow_result2['step_id']}")

    # Now try to save again with the SAME values (user didn't change anything)
    # This is where the "expected str" error should occur
    second_save_input = {
        "name": "testgruppe21",
        "indoor_temperature_sensor": "sensor.temp_kitchen",
        "diffuse_factor": "-1",  # Same values as before
        "threshold_direct": "-1",
        "threshold_diffuse": "500",  # This is the field from the screenshot
        "temperature_indoor_base": "-1",
        "temperature_outdoor_base": "-1",
    }

    try:
        second_save_result = await hass.config_entries.options.async_configure(
            flow_result2["flow_id"], user_input=second_save_input
        )
        print(f"✅ Second save result: {second_save_result['type']}")

        # If we get here, the bug might be fixed
        assert second_save_result["type"] == "create_entry"
        print("🎉 No error! The fix might be working.")

    except Exception as e:
        if "expected str" in str(e):
            print(f"🎯 FOUND THE BUG! Error: {e}")
            pytest.fail(f"Found the 'expected str' error: {e}")
        else:
            print(f"❌ Different error: {e}")
            raise


if __name__ == "__main__":
    import asyncio
    import logging

    # Enable debug logging
    logging.basicConfig(level=logging.DEBUG)

    # This test should be run with pytest normally
    print("Run this test with: python -m pytest tests/test_second_save_bug.py -v -s")
