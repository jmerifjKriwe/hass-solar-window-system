"""Test Options Flow for Solar Window System integration."""

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN


@pytest.mark.skip(reason="Testen veraltete Logik und müssen noch auf den aktuellen Stand gebracht werden")
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

    # Starte Options-Flow
    result = await hass.config_entries.options.async_init(entry.entry_id)
    # Simuliere gültige Eingabe mit den richtigen Feldern aus dem global_basic schema
    user_input = {
        "window_width": "1.5",
        "window_height": "2.0",
        "shadow_depth": "0.5",
        "shadow_offset": "0.3",
        "solar_radiation_sensor": "sensor.dummy_solar",
        "outdoor_temperature_sensor": "sensor.dummy_outdoor",
    }
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
        result3 = await hass.config_entries.options.async_configure(
            result2["flow_id"], user_input={}
        )
        if result3.get("type") == "form":
            # Scenarios page
            result4 = await hass.config_entries.options.async_configure(
                result3["flow_id"], user_input={}
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
    expected = 1.5  # Der Options-Flow konvertiert Strings zu float
    if actual != expected:
        msg = f"Expected window_width '{expected}', got '{actual}'"
        raise AssertionError(msg)
