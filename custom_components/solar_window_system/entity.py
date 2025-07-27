# /config/custom_components/solar_window_system/entity.py

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import SolarWindowDataUpdateCoordinator


class SolarWindowSystemDataEntity(CoordinatorEntity[SolarWindowDataUpdateCoordinator]):
    """Base class for entities that receive data from the coordinator."""

    _attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        """Return information about the device."""
        return DeviceInfo(
            identifiers={(DOMAIN, "solar_window_system_device")},
            name="Solar Window System",
            manufacturer="Custom Integration",
        )


class SolarWindowSystemConfigEntity:
    """Base class for configuration entities (number, select, switch)."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize the config entity."""
        self.hass = hass
        self.entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        """Return information about the device."""
        return DeviceInfo(
            identifiers={(DOMAIN, "solar_window_system_device")},
        )
