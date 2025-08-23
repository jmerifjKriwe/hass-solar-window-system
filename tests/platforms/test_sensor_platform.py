"""Test the sensor platform setup for Solar Window System (migrated)."""

from collections.abc import Iterable

import pytest
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN
from custom_components.solar_window_system.sensor import async_setup_entry


@pytest.mark.asyncio
async def test_sensor_platform_setup(hass) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Solar Window System",
        data={"entry_type": "global_config"},
        entry_id="test_sensor_setup",
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

    if len(added_entities) == 0:
        raise AssertionError("No sensor entities registered")
    for entity in added_entities:
        if not hasattr(entity, "_attr_unique_id"):
            raise AssertionError("Entity has no unique_id")


"""Test the Sensor platform setup for Solar Window System integration."""

import pytest
from homeassistant.core import HomeAssistant


@pytest.mark.asyncio
async def test_sensor_platform_setup(hass: HomeAssistant) -> None:
    """Ensure sensor entities are registered."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Solar Window System",
        data={"entry_type": "global_config"},
        entry_id="test_sensor_setup",
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

    if len(added_entities) == 0:
        raise AssertionError("No sensor entities registered")
    for entity in added_entities:
        if not hasattr(entity, "_attr_unique_id"):
            raise AssertionError("Entity missing unique_id")
