"""Test the setup of the BinarySensor platform for the Solar Window System integration."""

from collections.abc import Iterable

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.binary_sensor import async_setup_entry
from custom_components.solar_window_system.const import DOMAIN


@pytest.mark.asyncio
async def test_binary_sensor_platform_setup(hass: HomeAssistant) -> None:
    """Test that BinarySensor entities are registered properly."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Solar Window System",
        data={"entry_type": "global_config"},
        entry_id="test_binary_sensor_setup",
    )
    entry.add_to_hass(hass)

    # Create device registry entry for global configuration
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

    # For global configuration no BinarySensor entities are expected
    msg = "For global configuration no BinarySensor entities should be registered."
    if len(added_entities) != 0:
        raise AssertionError(msg)
