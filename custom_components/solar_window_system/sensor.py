"""Sensor entities for Solar Window System."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    ENERGY_TYPE_COMBINED,
    ENERGY_TYPE_DIFFUSE,
    ENERGY_TYPE_DIRECT,
    LEVEL_GROUP,
    LEVEL_WINDOW,
)
from .coordinator import SolarCalculationCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up sensor entities from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities = []

    # Create entities for each window
    for window_id in coordinator.windows:
        for energy_type in [
            ENERGY_TYPE_DIRECT,
            ENERGY_TYPE_DIFFUSE,
            ENERGY_TYPE_COMBINED,
        ]:
            entities.append(SolarEnergySensor(coordinator, LEVEL_WINDOW, window_id, energy_type))

    # Create entities for each group
    for group_id in coordinator.groups:
        for energy_type in [
            ENERGY_TYPE_DIRECT,
            ENERGY_TYPE_DIFFUSE,
            ENERGY_TYPE_COMBINED,
        ]:
            entities.append(SolarEnergySensor(coordinator, LEVEL_GROUP, group_id, energy_type))

    # Create entities for global
    for energy_type in [ENERGY_TYPE_DIRECT, ENERGY_TYPE_DIFFUSE, ENERGY_TYPE_COMBINED]:
        entities.append(SolarEnergySensor(coordinator, "global", "global", energy_type))

    async_add_entities(entities)


class SolarEnergySensor(CoordinatorEntity, SensorEntity):
    """Sensor for solar energy measurements."""

    coordinator: SolarCalculationCoordinator

    def __init__(
        self,
        coordinator: SolarCalculationCoordinator,
        level: str,
        name_id: str,
        energy_type: str,
    ) -> None:
        """Initialize the sensor.

        Args:
            coordinator: DataUpdateCoordinator instance
            level: One of LEVEL_WINDOW, LEVEL_GROUP, or "global"
            name_id: Identifier for the entity (window_id, group_id, or "global")
            energy_type: One of ENERGY_TYPE_DIRECT, ENERGY_TYPE_DIFFUSE, ENERGY_TYPE_COMBINED
        """
        super().__init__(coordinator)
        self._level = level
        self._name_id = name_id
        self._energy_type = energy_type

    @property
    def unique_id(self):
        """Return a unique ID for this sensor."""
        return f"{DOMAIN}_{self._level}_{self._name_id}_{self._energy_type}"

    @property
    def name(self):
        """Return the name of the sensor."""
        if self._level == LEVEL_WINDOW:
            display_name = self.coordinator.windows.get(self._name_id, {}).get(
                "name", self._name_id
            )
        elif self._level == LEVEL_GROUP:
            display_name = self.coordinator.groups.get(self._name_id, {}).get("name", self._name_id)
        else:
            display_name = "Global"

        energy_labels = {
            ENERGY_TYPE_DIRECT: "Direkte Energie",
            ENERGY_TYPE_DIFFUSE: "Diffuse Energie",
            ENERGY_TYPE_COMBINED: "Kombinierte Energie",
        }
        return f"{display_name} {energy_labels.get(self._energy_type, self._energy_type)}"

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return UnitOfPower.WATT

    @property
    def device_class(self):
        """Return the device class."""
        return SensorDeviceClass.POWER

    @property
    def state_class(self):
        """Return the state class for statistics."""
        return "measurement"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        # Get the data key based on level
        if self._level == LEVEL_GROUP:
            data_key = f"group_{self._name_id}"
        else:
            data_key = self._name_id

        # Get the data from coordinator
        if self.coordinator.data and data_key in self.coordinator.data:
            return self.coordinator.data[data_key].get(self._energy_type)

        return None

    @property
    def device_info(self):
        """Return device information."""
        if self._level == "global":
            return DeviceInfo(
                identifiers={(DOMAIN, DOMAIN)},
                name="Solar Window System",
                manufacturer="Solar Window System",
            )
        elif self._level == LEVEL_GROUP:
            group_name = self.coordinator.groups.get(self._name_id, {}).get("name", self._name_id)
            return DeviceInfo(
                identifiers={(DOMAIN, f"group_{self._name_id}")},
                name=f"Gruppe: {group_name}",
                manufacturer="Solar Window System",
                via_device=(DOMAIN, "global"),
            )
        else:  # window
            window_name = self.coordinator.windows.get(self._name_id, {}).get("name", self._name_id)
            return DeviceInfo(
                identifiers={(DOMAIN, f"window_{self._name_id}")},
                name=f"Fenster: {window_name}",
                manufacturer="Solar Window System",
                via_device=(DOMAIN, "global"),
            )
