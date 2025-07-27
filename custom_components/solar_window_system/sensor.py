# /config/custom_components/solar_window_system/sensor.py
import logging  # <-- HINZUGEFÜGT

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import SolarWindowDataUpdateCoordinator
from .entity import SolarWindowSystemDataEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor entities."""
    coordinator: SolarWindowDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    if coordinator.data is None:
        _LOGGER.debug(
            "Coordinator data is not yet available. Sensor setup will be deferred."
        )
        return

    summary_sensors = [SolarWindowSummarySensor(coordinator)]

    window_sensors = [
        SolarWindowPowerSensor(coordinator, window_id)
        for window_id in coordinator.data
        if window_id != "summary"
    ]

    async_add_entities(summary_sensors + window_sensors)


class SolarWindowSummarySensor(SolarWindowSystemDataEntity, SensorEntity):
    """Representation of the summary sensor."""

    def __init__(self, coordinator: SolarWindowDataUpdateCoordinator):
        """Initialize the summary sensor."""
        super().__init__(coordinator)
        self._attr_name = "Summary Power"
        self._attr_unique_id = f"{DOMAIN}_summary_power"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "W"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        value = self.coordinator.data.get("summary", {}).get("total_power")
        return round(value, 1) if isinstance(value, (int, float)) else None

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        summary = self.coordinator.data.get("summary", {})
        return {
            "window_count": summary.get("window_count"),
            "shading_count": summary.get("shading_count"),
            "last_calculation": summary.get("calculation_time"),
        }


class SolarWindowPowerSensor(SolarWindowSystemDataEntity, SensorEntity):
    """Representation of a power sensor for a single window."""

    def __init__(self, coordinator: SolarWindowDataUpdateCoordinator, window_id: str):
        """Initialize the window sensor."""
        super().__init__(coordinator)
        self._window_id = window_id

        self._attr_name = (
            f"{coordinator.data[self._window_id].get('name', window_id)} Power"
        )
        self._attr_unique_id = f"{DOMAIN}_{window_id}_power"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "W"
        self._attr_icon = "mdi:window-maximize"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        value = self.coordinator.data.get(self._window_id, {}).get("power_total")
        return round(value, 1) if isinstance(value, (int, float)) else None

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        window_data = self.coordinator.data.get(self._window_id, {})
        return {
            "power_direct": round(window_data.get("power_direct", 0), 1),
            "power_diffuse": round(window_data.get("power_diffuse", 0), 1),
            "area_m2": window_data.get("area_m2"),
        }
