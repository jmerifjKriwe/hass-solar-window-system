"""Test invalid value handling in Solar Window System config flow."""

from homeassistant import config_entries

from custom_components.solar_window_system.const import DOMAIN
from tests.test_data import INVALID_GLOBAL_BASIC


async def test_config_flow_invalid_value(hass) -> None:
    """Test that invalid numeric values are rejected in the config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result.get("type") == "form", f"Expected form, got: {result}"
    assert result.get("step_id") == "global_basic", (
        f"Expected global_basic step, got: {result.get('step_id')}"
    )

    user_input = INVALID_GLOBAL_BASIC.copy()
    user_input["window_width"] = "0.05"  # Must be >= 0.1
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=user_input
    )
    assert result2.get("type") == "form", f"Expected form with errors, got: {result2}"
    errors = result2.get("errors")
    assert errors and "window_width" in errors, (
        f"Expected error for window_width, got: {errors}"
    )
