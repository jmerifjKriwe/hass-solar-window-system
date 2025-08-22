"""Config flow tests (PoC) for global config flow."""

from __future__ import annotations

import pytest
from homeassistant import config_entries

from custom_components.solar_window_system.const import DOMAIN
from tests.test_data import VALID_GLOBAL_BASIC


@pytest.mark.asyncio
async def test_global_config_flow_init_shows_basic_step(hass) -> None:
    """Starting the config flow should show the global_basic step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result.get("type") == "form"
    assert result.get("step_id") == "global_basic"
