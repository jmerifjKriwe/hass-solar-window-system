"""
Test diagnostics endpoint for Solar Window System integration.

This file contains a snapshot test for the config entry diagnostics output.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN
from custom_components.solar_window_system.diagnostics import (
    async_get_config_entry_diagnostics,
)
from tests.helpers.snapshot import assert_matches_snapshot
from tests.helpers.test_framework import BaseTestCase

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


class TestDiagnostics(BaseTestCase):
    """Test diagnostics endpoint for Solar Window System integration."""

    test_type = "diagnostics"

    def get_required_fixtures(self) -> list[str]:
        """Return list of required fixture names for this test type."""
        return ["hass"]

    async def test_config_entry_snapshot(self, hass: HomeAssistant) -> None:
        """
        Snapshot test for config entry diagnostics output.

        This will create the initial snapshot when run for the first time.
        """
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Solar Window System",
            data={
                "entry_type": "global_config",
                "window_width": 1.5,
                "window_height": 2.0,
                "g_value": 0.6,
                "diffuse_factor": 0.2,
                "threshold_direct": 250,
                "threshold_diffuse": 120,
                "temperature_indoor_base": 22.0,
                "temperature_outdoor_base": 20.0,
            },
            source="user",
            entry_id="test_entry_id",
        )
        entry.add_to_hass(hass)

        result = await async_get_config_entry_diagnostics(hass, entry)
        # Convert mappingproxy to dict for JSON serialization
        result_dict = {
            "entry_data": dict(result["entry_data"]),
            "data": result["data"],
        }
        # Use snapshot assertion for diagnostics output
        assert_matches_snapshot("config_entry_diagnostics", result_dict)
