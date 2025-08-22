"""PoC tests for subentry flows: group and window."""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.config_flow import GroupSubentryFlowHandler, WindowSubentryFlowHandler
from custom_components.solar_window_system.const import DOMAIN


@pytest.mark.asyncio
async def test_group_subentry_handler_user_flow(hass) -> None:
    """Instantiate GroupSubentryFlowHandler and ensure user step form is shown."""
    parent = MockConfigEntry(domain=DOMAIN, data={"entry_type": "group_configs", "is_subentry_parent": True}, title="Group configurations")
    parent.add_to_hass(hass)

    handler = GroupSubentryFlowHandler()
    handler.hass = hass
    handler.parent_entry = parent

    result = await handler.async_step_user(None)
    assert result["type"] == "form"


@pytest.mark.asyncio
async def test_window_subentry_handler_user_flow(hass) -> None:
    """Instantiate WindowSubentryFlowHandler and ensure user step form is shown."""
    parent = MockConfigEntry(domain=DOMAIN, data={"entry_type": "window_configs", "is_subentry_parent": True}, title="Window configurations")
    parent.add_to_hass(hass)

    handler = WindowSubentryFlowHandler()
    handler.hass = hass
    handler.parent_entry = parent

    result = await handler.async_step_user(None)
    assert result["type"] == "form"
