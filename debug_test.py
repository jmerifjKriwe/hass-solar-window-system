#!/usr/bin/env python3
"""Debug script to reproduce the exact 'expected str' error from the screenshot."""

import asyncio
import sys
import logging
from pathlib import Path

# Add the custom components path
sys.path.insert(0, str((Path(__file__).parent / "custom_components").resolve()))

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN
from custom_components.solar_window_system.options_flow import (
    SolarWindowSystemOptionsFlow,
)

# Set up logging to see debug output
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")


async def debug_expected_str_error():
    """Reproduce the exact scenario from the screenshot."""
    print("🔍 Reproducing 'expected str' error from screenshot...")

    # Create a mock hass instance
    hass = MockHass()

    # Create config entry with the exact values shown in screenshot
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="testgruppe21",
        data={
            "entry_type": "group",
            "name": "testgruppe21",
            "indoor_temperature_sensor": "Temperatur Kueche",
            # These numeric values match the screenshot
            "diffuse_factor": -1,  # int sentinel value
            "threshold_direct": -1,  # int sentinel value
            "threshold_diffuse": 500,  # int value as shown
            "temperature_indoor_base": -1,  # int sentinel value
            "temperature_outdoor_base": -1,  # int sentinel value
        },
        options={},
        unique_id="debug_test_group",
    )

    print(f"📝 Config entry data: {config_entry.data}")

    # Create options flow directly (like in real usage)
    flow = SolarWindowSystemOptionsFlow(config_entry)
    flow.hass = hass

    try:
        print("🚀 Starting options flow...")
        # This should trigger the schema creation with numeric defaults
        result = await flow.async_step_init(user_input=None)

        print(f"✅ Schema creation successful: {result['type']}")
        print(f"📋 Step ID: {result['step_id']}")

        # Now simulate user clicking OK with the same values (this is where error occurs)
        print("\n🎯 Simulating user submission with same values...")
        user_input = {
            "name": "testgruppe21",
            "indoor_temperature_sensor": "Temperatur Kueche",
            "diffuse_factor": "-1",  # String versions as they come from UI
            "threshold_direct": "-1",
            "threshold_diffuse": "500",  # This field shows the error in screenshot
            "temperature_indoor_base": "-1",
            "temperature_outdoor_base": "-1",
        }

        print(f"📤 User input: {user_input}")

        # This is where the "expected str" error should occur
        result2 = await flow.async_step_group_options(user_input=user_input)

        print(f"✅ Submission successful: {result2['type']}")
        if result2["type"] == "form":
            print(f"❌ Errors: {result2.get('errors', {})}")

    except Exception as e:
        print(f"💥 ERROR: {e}")
        print(f"🔍 Error type: {type(e)}")
        import traceback

        traceback.print_exc()

        # Check if it's the expected str error
        if "expected str" in str(e):
            print("🎯 Found the 'expected str' error!")
            return True

    return False


class MockHass:
    """Minimal mock for HomeAssistant."""

    def __init__(self):
        self.config_entries = MockConfigEntries()


class MockConfigEntries:
    """Mock config entries."""

    def async_entries(self, domain=None):
        return []


if __name__ == "__main__":
    result = asyncio.run(debug_expected_str_error())
    if result:
        print("\n🎯 Successfully reproduced the 'expected str' error!")
        sys.exit(1)
    else:
        print("\n✅ No 'expected str' error found - the fix might be working!")
        sys.exit(0)
