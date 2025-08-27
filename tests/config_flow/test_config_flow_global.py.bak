"""Config flow tests (PoC) for global config flow."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from homeassistant import config_entries

from custom_components.solar_window_system.const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


@pytest.mark.asyncio
async def test_global_config_flow_init_shows_basic_step(hass: HomeAssistant) -> None:
    """
    Starting the config flow should show the global_basic step.

    This ensures the initial step_id is `global_basic` for the global entry.
    """
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    # ConfigFlowResult behaves like a mapping for our checks
    assert result.get("type") == "form"
    assert result.get("step_id") == "global_basic"
