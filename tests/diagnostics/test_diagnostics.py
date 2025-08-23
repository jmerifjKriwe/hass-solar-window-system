"""Test diagnostics endpoint for Solar Window System integration.

This file contains a snapshot test for the config entry diagnostics output.
"""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from syrupy.assertion import SnapshotAssertion

from custom_components.solar_window_system.diagnostics import (
    async_get_config_entry_diagnostics,
)
from custom_components.solar_window_system.const import DOMAIN


@pytest.mark.asyncio
async def test_diagnostics_config_entry_snapshot(
    hass: HomeAssistant, snapshot: SnapshotAssertion
) -> None:
    """Snapshot test for config entry diagnostics output.

    This will create the initial snapshot when run with `--snapshot-update`.
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
    assert result == snapshot
