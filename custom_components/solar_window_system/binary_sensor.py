"""Binary sensor platform for Solar Window System (window subentries)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up binary sensors for window subentries."""
    if entry.data.get("entry_type") != "window_configs":
        return

    _LOGGER.info("Setting up Window Configuration binary sensors")

    device_registry = dr.async_get(hass)

    if not entry.subentries:
        _LOGGER.warning("No window subentries found")
        return

    for subentry_id, subentry in entry.subentries.items():
        if subentry.subentry_type != "window":
            continue

        window_name = subentry.title
        window_device = None

        # Find device for this window subentry
        for device in device_registry.devices.values():
            device_has_entry = (
                device.config_entries and entry.entry_id in device.config_entries
            )
            subentries = device.config_entries_subentries
            device_has_subentry = (
                subentries
                and entry.entry_id in subentries
                and subentry_id in subentries[entry.entry_id]
            )
            if device_has_entry and device_has_subentry:
                for identifier in device.identifiers:
                    if (
                        identifier[0] == DOMAIN
                        and identifier[1] == f"window_{subentry_id}"
                    ):
                        window_device = device
                        break
                if window_device:
                    break

        if not window_device:
            _LOGGER.warning("Window device not found for: %s", window_name)
            continue

        entity = WindowShadingRequiredBinarySensor(window_device, window_name)
        async_add_entities([entity], config_subentry_id=subentry_id)


class WindowShadingRequiredBinarySensor(BinarySensorEntity):
    """Binary sensor indicating if shading is required for a window."""

    def __init__(self, device: dr.DeviceEntry, window_name: str) -> None:
        """Initialize the shading_required binary sensor for a window."""
        window_slug = window_name.lower().replace(" ", "_").replace("-", "_")
        self._attr_unique_id = f"sws_window_{window_slug}_shading_required"
        self._attr_suggested_object_id = f"sws_window_{window_slug}_shading_required"
        # Original name with prefix for traceability; friendly name will be overridden
        self._attr_name = f"SWS_WINDOW {window_name} Shading Required"
        self._attr_has_entity_name = False
        self._attr_device_info = {
            "identifiers": device.identifiers,
            "name": device.name,
            "manufacturer": device.manufacturer,
            "model": device.model,
        }
        self._attr_is_on = False
        self._attr_icon = "mdi:shield-sun"
        self._friendly_label = "Shading Required"

    @property
    def is_on(self) -> bool:
        """Return True if shading is currently required."""
        return bool(self._attr_is_on)

    async def async_added_to_hass(self) -> None:
        """Set a clean friendly name without prefixes (like the Selects)."""
        await super().async_added_to_hass()
        entity_registry = er.async_get(self.hass)
        if self.entity_id in entity_registry.entities:
            ent_reg_entry = entity_registry.entities[self.entity_id]
            new_friendly_name = self._friendly_label
            if ent_reg_entry.original_name != new_friendly_name:
                entity_registry.async_update_entity(
                    self.entity_id, name=new_friendly_name
                )
