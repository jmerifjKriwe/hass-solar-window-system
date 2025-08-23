"""Test reconfigure flow for the global configuration entry."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN
from tests.test_data import (
    VALID_GLOBAL_BASIC,
    VALID_GLOBAL_ENHANCED,
    VALID_GLOBAL_SCENARIOS,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


@pytest.mark.asyncio
async def test_global_config_reconfigure_flow(
    hass: HomeAssistant, enable_custom_integrations: None
) -> None:
    """
    Reconfiguring an existing global entry should show the options flow and accept new values.

    The global configuration is exposed via the OptionsFlow (not a ConfigFlow reconfigure
    handler). Use the options API to exercise the three option pages.
    """
    # Create an existing global config entry
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"entry_type": "global_config"},
        title="Solar Window System",
        entry_id="global_config_entry_id",
    )
    entry.add_to_hass(hass)

    # Start Options Flow for the entry
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == "form"
    assert result["step_id"] == "global_basic"

    # Submit basic values
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input=VALID_GLOBAL_BASIC
    )
    assert result["type"] == "form"
    assert result["step_id"] == "global_enhanced"

    # Submit enhanced values
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input=VALID_GLOBAL_ENHANCED
    )
    assert result["type"] == "form"
    assert result["step_id"] == "global_scenarios"

    # Submit scenarios to finish
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input=VALID_GLOBAL_SCENARIOS
    )
    assert result["type"] == "create_entry"
