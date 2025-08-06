from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import Entity

from .const import (
    CONF_GROUP,
    CONF_GROUP_NAME,
    DOMAIN,
    ENTITY_PREFIX_GLOBAL,
    ENTRY_TYPE_GROUP,
    GLOBAL_CONFIG_ENTITIES,
)
from .global_config import GlobalConfigSensor

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up sensors for Solar Window System."""
    # Handle group sensors (existing code)
    if entry.data.get("entry_type") == ENTRY_TYPE_GROUP:
        group_id = entry.data.get(CONF_GROUP, entry.entry_id)
        group_name = entry.data.get(CONF_GROUP_NAME, "Group")

        _LOGGER.debug(
            "[SolarWindowSystem] Adding dummy sensor entity for group: %s (%s)",
            group_name,
            group_id,
        )

        async_add_entities([SolarWindowSystemGroupDummySensor(group_id, group_name)])
        return

    # Handle Global Configuration sensors
    if entry.title == "Solar Window System":
        _LOGGER.info("Setting up Global Configuration sensors")

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
            sensors = []
            for entity_key, config in GLOBAL_CONFIG_ENTITIES.items():
                if config["platform"] == "sensor":
                    sensors.append(
                        GlobalConfigSensor(entity_key, config, global_device)
                    )

            if sensors:
                async_add_entities(sensors)
                _LOGGER.info("Added %d Global Configuration sensors", len(sensors))
        else:
            _LOGGER.warning("Global Configuration device not found")


class SolarWindowSystemGroupDummySensor(Entity):
    """Dummy sensor for group configurations."""

    def __init__(self, group_id: str, group_name: str) -> None:
        """Initialize the dummy group sensor."""
        self._attr_name = f"Dummy Group Sensor ({group_name})"
        self._attr_unique_id = f"{DOMAIN}_group_{group_id}_dummy"
        # device_info must match the device created in __init__.py
        self._attr_device_info = {
            "identifiers": {(DOMAIN, group_id)},
            "name": group_name,
            "manufacturer": "Solar Window System",
            "model": "Group",
        }

    @property
    def state(self) -> int:
        """Return the state of the sensor."""
        return 42
