from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_ENTRY_TYPE, CONF_WINDOW_NAME
from .coordinator import SolarWindowDataUpdateCoordinator


class SolarWindowSystemDataEntity(CoordinatorEntity[SolarWindowDataUpdateCoordinator]):
    """Base class for entities that receive data from the coordinator."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SolarWindowDataUpdateCoordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self.entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        """Return information about the device."""
        entry_type = self.entry.data.get(CONF_ENTRY_TYPE)
        if entry_type == "window":
            return DeviceInfo(
                identifiers={(DOMAIN, self.entry.entry_id)},
                name=self.entry.data.get(CONF_WINDOW_NAME, "Unnamed Window"),
                model="Virtual Window",
                manufacturer="Example GmbH",
            )
        # For global or group entries, return a generic device info
        return DeviceInfo(
            identifiers={(DOMAIN, "solar_window_system_global")},
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
        entry_type = self.entry.data.get(CONF_ENTRY_TYPE)
        if entry_type == "global":
            return DeviceInfo(
                identifiers={(DOMAIN, "solar_window_system_global")},
                name="Solar Window System",
                manufacturer="Custom Integration",
            )
        # For other entry types, return a generic device info or raise an error if not expected
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
        )