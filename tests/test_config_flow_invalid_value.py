"""Test invalid value handling in Solar Window System config flow."""

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from custom_components.solar_window_system.const import DOMAIN


@pytest.mark.asyncio
async def test_config_flow_invalid_value(hass: HomeAssistant) -> None:
    """Test that invalid numeric values are rejected in the config flow."""
    # Start config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Should get the global_basic form
    if result.get("type") != "form":
        msg = f"Expected form, got: {result}"
        raise AssertionError(msg)
    if result.get("step_id") != "global_basic":
        msg = f"Expected global_basic step, got: {result.get('step_id')}"
        raise AssertionError(msg)

    # Submit with invalid values (too small)
    user_input = {
        "window_width": "0.05",  # Must be >= 0.1
        "window_height": "2.0",  # Valid
        "shadow_depth": "0.5",  # Valid
        "shadow_offset": "0.3",  # Valid
        "solar_radiation_sensor": "sensor.dummy_solar",
        "outdoor_temperature_sensor": "sensor.dummy_outdoor",
        # Optionale Sensoren nicht einbeziehen, da leere Strings ungültig sind
    }

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=user_input
    )

    # Should return form with errors due to invalid value
    if result2.get("type") != "form":
        msg = f"Expected form with errors, got: {result2}"
        raise AssertionError(msg)

    # Should have error for window_width field
    errors = result2.get("errors")
    if not errors or "window_width" not in errors:
        msg = f"Expected error for window_width, got: {errors}"
        raise AssertionError(msg)
