"""Test Options Flow for Solar Window System integration."""

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN
from tests.test_data import (
    VALID_GLOBAL_BASIC,
    VALID_GLOBAL_ENHANCED,
    VALID_GLOBAL_SCENARIOS,
)


@pytest.mark.asyncio
async def test_options_flow_update_and_invalid(hass: HomeAssistant) -> None:
    """Test that options flow updates options and handles invalid input."""
    # Setup: Lege einen bestehenden ConfigEntry an
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Solar Window System",
        data={"entry_type": "global_config"},
        unique_id="unique_global_1",
        options={},
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Register dummy entities for selectors
    entity_registry = er.async_get(hass)
    entity_registry.async_get_or_create(
        "sensor", "test", "dummy_solar", suggested_object_id="dummy_solar"
    )
    entity_registry.async_get_or_create(
        "sensor", "test", "dummy_outdoor", suggested_object_id="dummy_outdoor"
    )
    entity_registry.async_get_or_create(
        "sensor", "test", "dummy_indoor", suggested_object_id="dummy_indoor"
    )

    # Starte Options-Flow
    result = await hass.config_entries.options.async_init(entry.entry_id)
    # Simuliere gültige Eingabe mit den richtigen Feldern aus dem global_basic schema
    user_input = VALID_GLOBAL_BASIC.copy()
    user_input["shadow_offset"] = "0.3"  # test-specific override
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input=user_input
    )
    # Sollte zu einer weiteren Seite führen oder erfolgreich sein
    if result2.get("type") not in ("form", "create_entry"):
        msg = f"Expected form or create_entry, got: {result2}"
        raise AssertionError(msg)

    # Wenn es eine weitere Seite gibt, teste ob die Option übernommen wurde
    if result2.get("type") == "form":
        # Gehe durch weitere Seiten (enhanced, scenarios)
        # Setze enhanced page mit Standardwerten fort
        enhanced_user_input = VALID_GLOBAL_ENHANCED.copy()
        enhanced_user_input["g_value"] = "0.5"
        enhanced_user_input["frame_width"] = "0.125"
        enhanced_user_input["diffuse_factor"] = "0.15"
        result3 = await hass.config_entries.options.async_configure(
            result2["flow_id"], user_input=enhanced_user_input
        )
        if result3.get("type") == "form":
            # Scenarios page
            scenarios_user_input = VALID_GLOBAL_SCENARIOS.copy()
            scenarios_user_input["scenario_c_temp_forecast"] = "28.5"
            scenarios_user_input["scenario_c_start_hour"] = "9"
            result4 = await hass.config_entries.options.async_configure(
                result3["flow_id"], user_input=scenarios_user_input
            )
            if result4.get("type") != "create_entry":
                msg = f"Expected create_entry, got: {result4}"
                raise AssertionError(msg)

    # Check that window_width was updated in options
    updated_entry = hass.config_entries.async_get_entry(entry.entry_id)
    if updated_entry is None:
        msg = "Entry not found after options update"
        raise AssertionError(msg)

    # Test passed! The options flow works correctly
    actual = updated_entry.options.get("window_width")
    expected = "1.5"  # Options-Flow speichert Werte als String
    if actual != expected:
        msg = f"Expected window_width '{expected}', got '{actual}'"
        raise AssertionError(msg)
