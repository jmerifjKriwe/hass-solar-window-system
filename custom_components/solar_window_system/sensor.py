from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.entity import Entity

from .const import DOMAIN, ENTRY_TYPE_GROUP, CONF_GROUP, CONF_GROUP_NAME

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up dummy group sensors for Solar Window System groups."""
    if entry.data.get("entry_type") != ENTRY_TYPE_GROUP:
        return

    group_id = entry.data.get(CONF_GROUP, entry.entry_id)
    group_name = entry.data.get(CONF_GROUP_NAME, "Group")

    _LOGGER.debug(
        "[SolarWindowSystem] Adding dummy sensor entity for group: %s (%s)",
        group_name,
        group_id,
    )

    async_add_entities([SolarWindowSystemGroupDummySensor(group_id, group_name)])


class SolarWindowSystemGroupDummySensor(Entity):
    def __init__(self, group_id: str, group_name: str) -> None:
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
        return 42
