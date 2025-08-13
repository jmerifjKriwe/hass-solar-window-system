"""Test duplicate config entry for Solar Window System integration."""

"""Test duplicate config entry for Solar Window System integration."""

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN


@pytest.mark.asyncio
async def test_config_flow_duplicate_entry(hass: HomeAssistant) -> None:
    """Test that creating a duplicate config entry is blocked."""
    # Create initial config entries to trigger "already_configured" condition

    # Create the main global config entry
    global_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Solar Window System",
        data={"entry_type": "global_config"},
        unique_id="unique_global_1",
    )
    global_entry.add_to_hass(hass)

    # Create group configs parent entry
    group_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Group configurations",
        data={"entry_type": "group_configs", "is_subentry_parent": True},
        unique_id="unique_group_parent",
    )
    group_entry.add_to_hass(hass)

    # Create window configs parent entry
    window_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Window configurations",
        data={"entry_type": "window_configs", "is_subentry_parent": True},
        unique_id="unique_window_parent",
    )
    window_entry.add_to_hass(hass)

    # Try to start a new config flow - should be blocked because all
    # required entries exist
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Should be aborted immediately due to already being configured
    if result.get("type") != "abort":
        msg = f"Expected abort, got: {result}"
        raise AssertionError(msg)
    if result.get("reason") != "already_configured":
        msg = f"Expected 'already_configured', got: {result.get('reason')}"
        raise AssertionError(msg)
