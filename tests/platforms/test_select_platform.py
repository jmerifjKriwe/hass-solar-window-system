"""Test the Select platform setup for Solar Window System integration."""

from collections.abc import Iterable

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN, GLOBAL_CONFIG_ENTITIES
from custom_components.solar_window_system.select import async_setup_entry


@pytest.mark.asyncio
async def test_select_platform_setup(hass: HomeAssistant) -> None:
    """Ensure select entities are registered when configured."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Solar Window System",
        data={"entry_type": "global_config"},
        entry_id="test_select_setup",
    )
    entry.add_to_hass(hass)

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

    has_input_select = any(
        config.get("platform") == "input_select"
        for config in GLOBAL_CONFIG_ENTITIES.values()
    )
    if has_input_select:
        if len(added_entities) == 0:
            raise AssertionError("No select entities registered")
        for entity in added_entities:
            if not hasattr(entity, "_attr_unique_id"):
                raise AssertionError("Entity missing unique_id")
    elif len(added_entities) != 0:
        raise AssertionError(
            "Select entities were registered but none expected by GLOBAL_CONFIG_ENTITIES"
        )
