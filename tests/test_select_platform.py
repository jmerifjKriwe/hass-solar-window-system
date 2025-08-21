"""Testet das Setup der Select-Plattform für die Solar Window System Integration."""

import pytest
from collections.abc import Iterable
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.solar_window_system.const import DOMAIN, GLOBAL_CONFIG_ENTITIES
from custom_components.solar_window_system.select import async_setup_entry


@pytest.mark.asyncio
async def test_select_platform_setup(hass: HomeAssistant) -> None:
    """Testet, ob Select-Entities korrekt registriert werden."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Solar Window System",
        data={"entry_type": "global_config"},
        entry_id="test_select_setup",
    )
    entry.add_to_hass(hass)

    # Device-Registry-Eintrag für globale Konfiguration anlegen
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "global_config")},
        name="Solar Window System Global Configuration",
        manufacturer="Solar Window System",
        model="Global Configuration",
    )

    added_entities = []

    def mock_async_add_entities(
        new_entities: Iterable,
        update_before_add: bool = False,
        *,
        config_subentry_id: str | None = None,
    ) -> None:
        added_entities.extend(new_entities)

    await async_setup_entry(hass, entry, mock_async_add_entities)

    # Prüfe, ob für die globale Konfiguration überhaupt Select-Entities definiert sind
    has_input_select = any(
        config.get("platform") == "input_select"
        for config in GLOBAL_CONFIG_ENTITIES.values()
    )
    if has_input_select:
        msg_no_entities = "Es wurden keine Select-Entities registriert."
        if len(added_entities) == 0:
            raise AssertionError(msg_no_entities)
        msg_no_uid = "Entity hat keine unique_id."
        for entity in added_entities:
            if not hasattr(entity, "_attr_unique_id"):
                raise AssertionError(msg_no_uid)
    else:
        # Es werden keine Select-Entities erwartet
        msg = (
            "Für die globale Konfiguration dürfen keine Select-Entities "
            "registriert werden, da keine input_select-Einträge in "
            "GLOBAL_CONFIG_ENTITIES definiert sind."
        )
        if len(added_entities) != 0:
            raise AssertionError(msg)
