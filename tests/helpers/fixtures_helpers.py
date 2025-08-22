"""Test helper fixtures for the Solar Window System tests.

Place reusable fixtures and helpers here so platform tests can be concise.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, List

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN


def create_global_config_entry(
    hass: HomeAssistant, entry_id: str = "test_entry"
) -> MockConfigEntry:
    """Create and add a MockConfigEntry for global config and return it."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Solar Window System",
        data={"entry_type": "global_config"},
        entry_id=entry_id,
    )
    entry.add_to_hass(hass)
    return entry


def ensure_global_device(hass: HomeAssistant, entry: MockConfigEntry):
    """Ensure the global device is present in the device registry and return it."""
    device_registry = dr.async_get(hass)
    return device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "global_config")},
        name="Solar Window System Global Configuration",
        manufacturer="Solar Window System",
        model="Global Configuration",
    )


async def collect_entities_for_setup(
    hass: HomeAssistant, module: Any, entry: MockConfigEntry
) -> List[Any]:
    """Call module.async_setup_entry and return a list of added entities.

    The module is expected to expose `async_setup_entry(hass, entry, async_add_entities)`.
    """
    added_entities: List[Any] = []

    def _mock_async_add_entities(
        new_entities: Iterable, update_before_add: bool = False, **kwargs
    ) -> None:
        # materialize iterator
        added_entities.extend(list(new_entities))

    await module.async_setup_entry(hass, entry, _mock_async_add_entities)
    return added_entities


@pytest.fixture
def global_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Pytest fixture that creates and returns a global MockConfigEntry."""
    return create_global_config_entry(hass)
