"""Sensor entities for Solar Window System."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import UnitOfPower
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    ENERGY_TYPE_COMBINED,
    ENERGY_TYPE_DIFFUSE,
    ENERGY_TYPE_DIRECT,
    LEVEL_GLOBAL,
    LEVEL_GROUP,
    LEVEL_WINDOW,
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up sensor entities from a config entry."""
    # Get coordinator and config from entry
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    config = hass.data[DOMAIN][entry.entry_id]["config"]

    entities = []

    # Create entities for each window
    for window_id in config.get("windows", {}).keys():
        for energy_type in [
            ENERGY_TYPE_DIRECT,
            ENERGY_TYPE_DIFFUSE,
            ENERGY_TYPE_COMBINED,
        ]:
            entities.append(
                SolarEnergySensor(
                    coordinator, config, LEVEL_WINDOW, window_id, energy_type
                )
            )

    # Create entities for each group
    for group_id in config.get("groups", {}).keys():
        for energy_type in [
            ENERGY_TYPE_DIRECT,
            ENERGY_TYPE_DIFFUSE,
            ENERGY_TYPE_COMBINED,
        ]:
            entities.append(
                SolarEnergySensor(
                    coordinator, config, LEVEL_GROUP, group_id, energy_type
                )
            )

    # Create entities for global
    for energy_type in [ENERGY_TYPE_DIRECT, ENERGY_TYPE_DIFFUSE, ENERGY_TYPE_COMBINED]:
        entities.append(
            SolarEnergySensor(coordinator, config, LEVEL_GLOBAL, "global", energy_type)
        )

    async_add_entities(entities)


class SolarEnergySensor(CoordinatorEntity, SensorEntity):
    """Sensor for solar energy measurements."""

    def __init__(self, coordinator, config, level, name_id, energy_type):
        """Initialize the sensor.

        Args:
            coordinator: DataUpdateCoordinator instance
            config: Configuration dictionary
            level: One of LEVEL_WINDOW, LEVEL_GROUP, LEVEL_GLOBAL
            name_id: Identifier for the entity (window_id, group_id, or "global")
            energy_type: One of ENERGY_TYPE_DIRECT, ENERGY_TYPE_DIFFUSE, ENERGY_TYPE_COMBINED
        """
        super().__init__(coordinator)
        self.config = config
        self.level = level
        self.name_id = name_id
        self.energy_type = energy_type

        # Get display name from config
        self._display_name = self._get_display_name()

    def _get_display_name(self):
        """Get the display name for this sensor."""
        if self.level == LEVEL_WINDOW:
            window = self.config.get("windows", {}).get(self.name_id, {})
            return window.get("name", self.name_id.replace("_", " ").title())
        elif self.level == LEVEL_GROUP:
            group = self.config.get("groups", {}).get(self.name_id, {})
            return group.get("name", self.name_id.replace("_", " ").title())
        else:  # LEVEL_GLOBAL
            return "Global"

    @property
    def unique_id(self):
        """Return a unique ID for this sensor."""
        return f"solar_window_system_{self.level}_{self.name_id}_{self.energy_type}"

    @property
    def name(self):
        """Return the name of the sensor."""
        energy_label = self.energy_type.replace("_", " ").title()
        return f"Solar Window System {self._display_name} {energy_label} Energy"

    @property
    def unit_of_measurement(self):
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
        if self.level == LEVEL_GROUP:
            data_key = f"group_{self.name_id}"
        else:
            data_key = self.name_id

        # Get the data from coordinator
        if self.coordinator.data and data_key in self.coordinator.data:
            return self.coordinator.data[data_key].get(self.energy_type)

        return None

    @property
    def device_info(self):
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, "solar_window_system")},
            name="Solar Window System",
            manufacturer="Solar Window System",
            model="Solar Energy Calculator",
        )
