"""Text platform for Solar Window System."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.text import TextEntity
from homeassistant.const import EntityCategory
from homeassistant.helpers.restore_state import RestoreEntity

from .global_config_entity import (
    GlobalConfigEntityBase,
    find_global_config_device,
    create_global_config_entities,
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
    """Set up text entities for Solar Window System."""
    # Only handle Global Configuration
    if entry.title != "Solar Window System":
        return

    global_device = find_global_config_device(hass, entry.entry_id)

    if global_device:
        text_entities = create_global_config_entities(
            GlobalConfigTextEntity, global_device, "input_text"
        )
        if text_entities:
            async_add_entities(text_entities)
    else:
        _LOGGER.warning("Global Configuration device not found")


class GlobalConfigTextEntity(GlobalConfigEntityBase, TextEntity, RestoreEntity):
    """Text entity for global configuration values."""

    def __init__(
        self,
        entity_key: str,
        config: dict,
        device,  # type: ignore[no-untyped-def]
    ) -> None:
        """Initialize the text entity."""
        # Initialize base class first
        super().__init__(entity_key, config, device)

        # Set text-specific attributes
        self._attr_native_max = config["max"]
        self._attr_native_value = config["default"]

        # Set entity category to diagnostic for debug entities
        if config.get("category") == "debug":
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    async def async_added_to_hass(self) -> None:
        """Call when entity is added to hass and restore previous state if available."""
        await super().async_added_to_hass()

        # Restore previous state if available
        restored_state = await self.async_get_last_state()
        if restored_state is not None and isinstance(restored_state.state, str):
            self._attr_native_value = restored_state.state

    async def async_set_value(self, value: str) -> None:
        """Update the current value and persist state."""
        self._attr_native_value = value
        self.async_write_ha_state()
