"""Switch platform for Solar Window System."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers import device_registry as dr

from .const import (
    DOMAIN,
    ENTITY_PREFIX_GLOBAL,
    GLOBAL_CONFIG_ENTITIES,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up switch entities for Solar Window System."""
    # Only handle Global Configuration
    if entry.title != "Solar Window System":
        return

    _LOGGER.info("Setting up Global Configuration switch entities")

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
        switch_entities = []
        for entity_key, config in GLOBAL_CONFIG_ENTITIES.items():
            if config["platform"] == "input_boolean":
                switch_entities.append(
                    GlobalConfigSwitchEntity(entity_key, config, global_device)
                )

        if switch_entities:
            async_add_entities(switch_entities)
            _LOGGER.info(
                "Added %d Global Configuration switch entities", len(switch_entities)
            )
    else:
        _LOGGER.warning("Global Configuration device not found")


class GlobalConfigSwitchEntity(SwitchEntity):
    """Switch entity for global configuration boolean values."""

    def __init__(
        self,
        entity_key: str,
        config: dict,
        device: dr.DeviceEntry,
    ) -> None:
        """Initialize the switch entity."""
        self._entity_key = entity_key
        self._config = config
        self._device = device
        # Set name, unique_id, and suggested_object_id for proper entity ID generation
        # WORKAROUND: Use prefixed name initially to get correct entity_id generation
        self._attr_name = f"{ENTITY_PREFIX_GLOBAL.upper()} {config['name']}"
        self._attr_unique_id = f"{ENTITY_PREFIX_GLOBAL}_{entity_key}"
        # Use suggested_object_id instead of entity_id to preserve prefix with unique_id
        self._attr_suggested_object_id = f"{ENTITY_PREFIX_GLOBAL}_{entity_key}"
        # Disable has_entity_name to ensure our suggested_object_id is used
        self._attr_has_entity_name = False
        # Store the original name for later restoration
        self._original_name = config["name"]

        _LOGGER.warning(
            "🔧 Switch %s: unique_id=%s, temp_name=%s",
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
        self._attr_icon = config.get("icon")
        self._attr_is_on = config["default"]

    async def async_added_to_hass(self) -> None:
        """Call when entity is added to hass."""
        await super().async_added_to_hass()
        # Restore the original name after entity ID has been generated
        self._attr_name = self._original_name
        _LOGGER.warning(
            "🔧 Switch %s registered, restoring name to: %s",
            self._entity_key,
            self._attr_name,
        )

    async def async_turn_on(self) -> None:
        """Turn the entity on."""
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self) -> None:
        """Turn the entity off."""
        self._attr_is_on = False
        self.async_write_ha_state()
