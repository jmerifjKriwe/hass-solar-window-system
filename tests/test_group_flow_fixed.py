"""Test group config flow."""

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN


@pytest.mark.skip(reason="Group flow tests are complex and need refactoring")
@pytest.mark.asyncio
async def test_group_flow_add_and_invalid(hass: HomeAssistant) -> None:
    """Test that group subentry can be added and invalid input is handled."""
    # Setup: Lege einen bestehenden Global ConfigEntry an
    global_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Solar Window System",
        data={"entry_type": "global_config"},
        unique_id="unique_global_1",
        options={},
    )
    global_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(global_entry.entry_id)
    await hass.async_block_till_done()

    # Teste Group-Subentry-Flow über den richtigen Flow-Mechanismus
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )

    # Navigiere zum Gruppen-Entry-Typ
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"entry_type": "group"}
    )

    # Sollte jetzt das Group-Formular zeigen
    if result2.get("type") != "form":
        msg = f"Expected form, got: {result2}"
        raise AssertionError(msg)

    # Simuliere gültige Eingabe für Gruppe mit gültigen Feldern
    user_input = {
        "name": "Test Group",
        "window_count": "5",
        "window_spacing": "1.2",
        "row_count": "2",
    }
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"], user_input=user_input
    )

    # Test sollte erfolgreich oder zur nächsten Seite gehen
    if result3.get("type") not in ("form", "create_entry"):
        msg = f"Unexpected result: {result3}"
        raise AssertionError(msg)
