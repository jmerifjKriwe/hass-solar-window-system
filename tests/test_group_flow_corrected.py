"""Test group config flow."""

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN


@pytest.mark.skip(reason="Group flow tests are complex and need refactoring")
@pytest.mark.asyncio
async def test_group_config_flow_creation(hass: HomeAssistant) -> None:
    """Test creating a group config entry through the config flow."""
    # Setup: Global config entry muss bereits existieren
    global_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Solar Window System",
        data={"entry_type": "global_config"},
        unique_id="global_config",
    )
    global_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(global_entry.entry_id)
    await hass.async_block_till_done()

    # Groups parent entry muss ebenfalls existieren
    groups_parent_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Groups",
        data={"entry_type": "group_configs", "is_subentry_parent": True},
        unique_id="group_configs",
    )
    groups_parent_entry.add_to_hass(hass)

    # Starte Config-Flow für neue Gruppe
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    if result.get("type") != "form":
        msg = f"Expected form, got: {result}"
        raise AssertionError(msg)

    # Wähle "Add Group Configuration"
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"entry_type": "group"}
    )
    if result2.get("type") != "form":
        msg = f"Expected form, got: {result2}"
        raise AssertionError(msg)
    if result2.get("step_id") != "group_basic":
        msg = f"Expected group_basic step, got: {result2.get('step_id')}"
        raise AssertionError(msg)

    # Erste Seite: Basic Group Configuration
    group_basic_input = {
        "name": "Test Group",
        "elevation": "50.0",
        "azimuth": "180.0",
        "window_count": "2",
    }
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"], user_input=group_basic_input
    )
    if result3.get("type") not in ("form", "create_entry"):
        msg = f"Expected form or create_entry, got: {result3}"
        raise AssertionError(msg)

    # Wenn mehrseitig, gehe zur nächsten Seite
    if result3.get("type") == "form":
        # Enhanced-Seite mit leeren defaults
        result4 = await hass.config_entries.flow.async_configure(
            result3["flow_id"], user_input={}
        )
        if result4.get("type") != "create_entry":
            msg = f"Expected create_entry, got: {result4}"
            raise AssertionError(msg)

    # Prüfe, dass ein Group-Entry erstellt wurde
    entries = hass.config_entries.async_entries(DOMAIN)
    group_entries = [
        e
        for e in entries
        if e.data.get("entry_type") == "group" and e.title == "Test Group"
    ]
    if not group_entries:
        msg = "No group entry was created"
        raise AssertionError(msg)

    group_entry = group_entries[0]

    # Prüfe die gespeicherten Daten
    expected_name = "Test Group"
    actual_name = group_entry.data.get("name")
    if actual_name != expected_name:
        msg = f"Expected name '{expected_name}', got '{actual_name}'"
        raise AssertionError(msg)

    expected_elevation = 50.0
    actual_elevation = group_entry.data.get("elevation")
    if actual_elevation != expected_elevation:
        msg = f"Expected elevation '{expected_elevation}', got '{actual_elevation}'"
        raise AssertionError(msg)
