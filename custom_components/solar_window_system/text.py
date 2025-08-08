"""Text platform for Solar Window System."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.text import TextEntity
from homeassistant.const import EntityCategory
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, ENTITY_PREFIX_GLOBAL, GLOBAL_CONFIG_ENTITIES

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up text entities for Solar Window System."""
    # Only handle Global Configuration
    if entry.title != "Solar Window System":
        return

    _LOGGER.info("Setting up Global Configuration text entities")

    device_registry = dr.async_get(hass)
    global_device = None

    # Find the global configuration device
    for device in device_registry.devices.values():
        if device.config_entries and entry.entry_id in device.config_entries:
            for identifier in device.identifiers:
                if identifier[0] == DOMAIN and identifier[1] == "global_config":
                    global_device = device
                    break
            if global_device:
                break

    if global_device:
        text_entities = []
        for entity_key, config in GLOBAL_CONFIG_ENTITIES.items():
            if config["platform"] == "input_text":
                text_entities.append(
                    GlobalConfigTextEntity(entity_key, config, global_device)
                )

        if text_entities:
            async_add_entities(text_entities)
            _LOGGER.info(
                "Added %d Global Configuration text entities", len(text_entities)
            )
    else:
        _LOGGER.warning("Global Configuration device not found")


class GlobalConfigTextEntity(TextEntity):
    """Text entity for global configuration values."""

    def __init__(
        self,
        entity_key: str,
        config: dict,
        device: dr.DeviceEntry,
    ) -> None:
        """Initialize the text entity."""
        self._entity_key = entity_key
        self._config = config
        self._device = device
        # Stable unique ID + desired object id
        self._attr_unique_id = f"{ENTITY_PREFIX_GLOBAL}_{entity_key}"
        self._attr_suggested_object_id = f"{ENTITY_PREFIX_GLOBAL}_{entity_key}"
        # Readable name, but don't let device name influence entity_id
        self._attr_name = f"SWS_GLOBAL {config['name']}"
        self._attr_has_entity_name = False

        _LOGGER.warning(
            "🔧 Text %s: unique_id=%s, name=%s",
            entity_key,
            self._attr_unique_id,
            self._attr_name,
        )
        self._attr_device_info = {
            "identifiers": device.identifiers,
            "name": device.name,
            "manufacturer": device.manufacturer,
            "model": device.model,
        }
        self._attr_native_max = config["max"]
        self._attr_icon = config.get("icon")
        self._attr_native_value = config["default"]

        # Set entity category to diagnostic for debug entities
        if config.get("category") == "debug":
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    async def async_added_to_hass(self) -> None:
        """Call when entity is added to hass."""
        await super().async_added_to_hass()
        _LOGGER.warning(
            "🔧 Text %s registered with name: %s",
            self._entity_key,
            self._attr_name,
        )

    async def async_set_value(self, value: str) -> None:
        """Update the current value."""
        self._attr_native_value = value
        self.async_write_ha_state()
