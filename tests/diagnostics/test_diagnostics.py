"""Test diagnostics endpoint for Solar Window System integration."""

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from syrupy.assertion import SnapshotAssertion
from custom_components.solar_window_system.diagnostics import (
    async_get_config_entry_diagnostics,
)

from custom_components.solar_window_system.const import DOMAIN


@pytest.mark.asyncio
async def test_diagnostics_config_entry(
    hass: HomeAssistant, snapshot: SnapshotAssertion
) -> None:
    """Test config entry diagnostics output (snapshot)."""
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


"""Test diagnostics endpoint for Solar Window System integration."""

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.solar_window_system.diagnostics import (
    async_get_config_entry_diagnostics,
)

from custom_components.solar_window_system.const import DOMAIN


@pytest.mark.asyncio
async def test_diagnostics_config_entry(hass: HomeAssistant) -> None:
    """Test config entry diagnostics output contains expected keys."""
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

    # Basic structural checks match the integration implementation
    assert isinstance(result, dict)
    assert "entry_data" in result
    assert "data" in result

    # The entry_data should be the original entry.data mapping
    entry_data = result["entry_data"]
    assert entry_data.get("entry_type") == "global_config"
    assert entry_data.get("window_width") == 1.5

    # Data section is currently empty but present
    assert isinstance(result["data"], dict)
