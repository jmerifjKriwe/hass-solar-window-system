"""Binary sensor entities for Solar Window System."""

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LEVEL_GROUP, LEVEL_WINDOW

if TYPE_CHECKING:
    from .coordinator import SolarCalculationCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up binary sensor entities from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities = []

    # Create shading recommendation sensors for each window
    for window_id in coordinator.windows:
        entities.append(ShadingRecommendationBinarySensor(coordinator, LEVEL_WINDOW, window_id))

    # Create shading recommendation sensors for each group
    for group_id in coordinator.groups:
        entities.append(ShadingRecommendationBinarySensor(coordinator, LEVEL_GROUP, group_id))

    # Create global shading recommendation sensor
    entities.append(ShadingRecommendationBinarySensor(coordinator, "global", "global"))

    async_add_entities(entities)


class ShadingRecommendationBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor indicating if shading is recommended."""

    coordinator: SolarCalculationCoordinator

    def __init__(self, coordinator: SolarCalculationCoordinator, level: str, entity_id: str):
        """Initialize the binary sensor.

        Args:
            coordinator: DataUpdateCoordinator instance
            level: One of LEVEL_WINDOW, LEVEL_GROUP, or "global"
            entity_id: Identifier for the entity (window_id, group_id, or "global")
        """
        super().__init__(coordinator)
        self._level = level
        self._entity_id = entity_id

    @property
    def unique_id(self):
        """Return a unique ID for this sensor."""
        return f"{DOMAIN}_{self._level}_{self._entity_id}_shading_recommended"

    @property
    def name(self):
        """Return the name of the sensor."""
        if self._level == LEVEL_WINDOW:
            display_name = self.coordinator.windows.get(self._entity_id, {}).get(
                "name", self._entity_id
            )
            return f"{display_name} Verschattung empfohlen"
        elif self._level == LEVEL_GROUP:
            display_name = self.coordinator.groups.get(self._entity_id, {}).get(
                "name", self._entity_id
            )
            return f"{display_name} Verschattung empfohlen"
        else:
            return "Global Verschattung empfohlen"

    @property
    def is_on(self):
        """Return True if shading is recommended."""
        # Get the data key based on level
        if self._level == LEVEL_GROUP:
            data_key = f"group_{self._entity_id}"
        else:
            data_key = self._entity_id

        # Get the data from coordinator
        if self.coordinator.data and data_key in self.coordinator.data:
            return self.coordinator.data[data_key].get("shading_recommended", False)

        return False

    @property
    def device_class(self):
        """Return the device class."""
        return BinarySensorDeviceClass.WINDOW

    @property
    def icon(self):
        """Return the icon based on state."""
        if self.is_on:
            return "mdi:blinds-closed"
        return "mdi:blinds-open"

    @property
    def device_info(self):
        """Return device information."""
        if self._level == "global":
            return DeviceInfo(
                identifiers={(DOMAIN, "global")},
                name="Solar Window System Global",
                manufacturer="Solar Window System",
            )
        elif self._level == LEVEL_GROUP:
            group_name = self.coordinator.groups.get(self._entity_id, {}).get(
                "name", self._entity_id
            )
            return DeviceInfo(
                identifiers={(DOMAIN, f"group_{self._entity_id}")},
                name=f"Gruppe: {group_name}",
                manufacturer="Solar Window System",
                via_device=(DOMAIN, "global"),
            )
        else:  # window
            window_name = self.coordinator.windows.get(self._entity_id, {}).get(
                "name", self._entity_id
            )
            return DeviceInfo(
                identifiers={(DOMAIN, f"window_{self._entity_id}")},
                name=f"Fenster: {window_name}",
                manufacturer="Solar Window System",
                via_device=(DOMAIN, "global"),
            )
