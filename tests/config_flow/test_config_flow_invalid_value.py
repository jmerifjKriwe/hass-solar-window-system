"""Tests for invalid value handling in the config flow."""

from typing import TYPE_CHECKING

import pytest
from homeassistant import config_entries

from custom_components.solar_window_system.const import DOMAIN
from tests.test_data import INVALID_GLOBAL_BASIC

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


@pytest.mark.asyncio
async def test_config_flow_invalid_value(hass: "HomeAssistant") -> None:
    """Invalid numeric values should be reported as form errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    if result.get("type") != "form":
        raise AssertionError(f"Expected form, got: {result}")
    if result.get("step_id") != "global_basic":
        raise AssertionError(
            f"Expected global_basic step, got: {result.get('step_id')}"
        )

    user_input = INVALID_GLOBAL_BASIC.copy()
    user_input["window_width"] = "0.05"  # Must be >= 0.1 per validators
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=user_input
    )
    if result2.get("type") != "form":
        raise AssertionError(f"Expected form with errors, got: {result2}")
    errors = result2.get("errors")
    if not errors or "window_width" not in errors:
        raise AssertionError(f"Expected error for window_width, got: {errors}")
