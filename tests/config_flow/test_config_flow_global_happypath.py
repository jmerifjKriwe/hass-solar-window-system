"""Integration-style tests for the global config flow (happy path)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.solar_window_system.const import DOMAIN
from tests.test_data import (
    VALID_GLOBAL_BASIC,
    VALID_GLOBAL_ENHANCED,
    VALID_GLOBAL_SCENARIOS,
)


if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


@pytest.mark.asyncio
async def test_global_config_flow_create_entry(hass: HomeAssistant) -> None:
    """Walk the global config flow through both steps and expect create_entry."""
    # Step 1: start flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result.get("type") == "form"
    assert result.get("step_id") == "global_basic"

    # Provide basic global data
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=VALID_GLOBAL_BASIC
    )
    assert result2.get("type") == "form"
    assert result2.get("step_id") == "global_enhanced"

    # Provide enhanced global data (step 2); next step is scenarios (step 3)
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"], user_input=VALID_GLOBAL_ENHANCED
    )
    assert result3.get("type") == "form"
    assert result3.get("step_id") == "global_scenarios"

    # Provide scenarios and expect create_entry
    result4 = await hass.config_entries.flow.async_configure(
        result3["flow_id"], user_input=VALID_GLOBAL_SCENARIOS
    )
    assert result4.get("type") == FlowResultType.CREATE_ENTRY
