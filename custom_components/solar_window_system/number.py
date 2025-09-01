"""Number platform for Solar Window System."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.number import NumberEntity
from homeassistant.helpers.restore_state import RestoreEntity

if TYPE_CHECKING:
    from homeassistant.helpers import device_registry as dr

from .global_config_entity import (
    GlobalConfigEntityBase,
    create_global_config_entities,
    find_global_config_device,
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
    """Set up number entities for Solar Window System."""
    # Only handle Global Configuration
    if entry.title != "Solar Window System":
        return

    global_device = find_global_config_device(hass, entry.entry_id)

    if global_device:
        number_entities = create_global_config_entities(
            GlobalConfigNumberEntity, global_device, "input_number"
        )
        if number_entities:
            async_add_entities(number_entities)
    else:
        _LOGGER.warning("Global Configuration device not found")


class GlobalConfigNumberEntity(GlobalConfigEntityBase, NumberEntity, RestoreEntity):
    """Number entity for global configuration values."""

    def __init__(
        self,
        entity_key: str,
        config: dict,
        device: dr.DeviceEntry,
    ) -> None:
        """Initialize the number entity."""
        # Initialize base class first
        super().__init__(entity_key, config, device)

        # Set number-specific attributes
        self._attr_native_min_value = config["min"]
        self._attr_native_max_value = config["max"]
        self._attr_native_step = config["step"]
        self._attr_native_unit_of_measurement = config.get("unit")
        self._attr_native_value = config["default"]

    async def async_added_to_hass(self) -> None:
        """Call when entity is added to hass and restore previous state if available."""
        await super().async_added_to_hass()

        # Restore previous state if available
        restored_state = await self.async_get_last_state()
        if restored_state is not None:
            try:
                value = float(restored_state.state)
                if self._attr_native_min_value <= value <= self._attr_native_max_value:
                    self._attr_native_value = value
            except (ValueError, TypeError):
                pass

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value and persist state."""
        self._attr_native_value = value
        self.async_write_ha_state()
