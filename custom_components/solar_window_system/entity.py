from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_ENTRY_TYPE, CONF_WINDOW_NAME, DOMAIN
from .coordinator import SolarWindowDataUpdateCoordinator


class SolarWindowSystemDataEntity(CoordinatorEntity[SolarWindowDataUpdateCoordinator]):
    """Base class for entities that receive data from the coordinator."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: SolarWindowDataUpdateCoordinator, entry: ConfigEntry
    ):
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
                configuration_url=f"/config/integrations/integration/{DOMAIN}",
            )
        if entry_type == "group":
            return DeviceInfo(
                identifiers={(DOMAIN, self.entry.entry_id)},
                name=self.entry.data.get("name", "Virtual Group"),
                model="Virtual Group",
                manufacturer="Example GmbH",
                configuration_url=f"/config/integrations/integration/{DOMAIN}",
            )
        # For global or other entries, return a generic device info
        return DeviceInfo(
            identifiers={(DOMAIN, "solar_window_system_global")},
            name="Solar Window System",
            manufacturer="Custom Integration",
            configuration_url=f"/config/integrations/integration/{DOMAIN}",
        )


class SolarWindowSystemConfigEntity:
    """Base class for configuration entities (number, select, switch)."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
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
        # For other entry types, return a generic device info
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
        )
