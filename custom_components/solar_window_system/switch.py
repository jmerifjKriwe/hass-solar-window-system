"""Switch platform for Solar Window System."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.switch import SwitchEntity
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
    """Set up switch entities for Solar Window System."""
    # Only handle Global Configuration
    if entry.title != "Solar Window System":
        return

    global_device = find_global_config_device(hass, entry.entry_id)

    if global_device:
        switch_entities = create_global_config_entities(
            GlobalConfigSwitchEntity, global_device, "input_boolean"
        )
        if switch_entities:
            async_add_entities(switch_entities)
    else:
        _LOGGER.warning("Global Configuration device not found")


class GlobalConfigSwitchEntity(GlobalConfigEntityBase, SwitchEntity, RestoreEntity):
    """Switch entity for global configuration boolean values."""

    def __init__(
        self,
        entity_key: str,
        config: dict,
        device,  # type: ignore[no-untyped-def]
    ) -> None:
        """Initialize the switch entity."""
        # Initialize base class first
        super().__init__(entity_key, config, device)

        # Set switch-specific attributes
        self._attr_is_on = config["default"]

    async def async_added_to_hass(self) -> None:
        """Call when entity is added to hass and restore previous state if available."""
        await super().async_added_to_hass()

        # Restore previous state if available
        restored_state = await self.async_get_last_state()
        if restored_state is not None:
            if restored_state.state.lower() in ("on", "true", "1"):
                self._attr_is_on = True
            elif restored_state.state.lower() in ("off", "false", "0"):
                self._attr_is_on = False

    async def async_turn_on(self) -> None:  # type: ignore[override]
        """Turn the entity on and persist state."""
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self) -> None:  # type: ignore[override]
        """Turn the entity off and persist state."""
        self._attr_is_on = False
        self.async_write_ha_state()
