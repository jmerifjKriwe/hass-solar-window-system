# /config/custom_components/solar_window_system/sensor.py
import logging

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

    # Data should now be available after async_config_entry_first_refresh
    if coordinator.data is None:
        _LOGGER.info("Coordinator data is None")
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
        if self.coordinator.data is None:
            return None
        value = self.coordinator.data.get("summary", {}).get("total_power")
        return round(value, 1) if isinstance(value, (int, float)) else None

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if self.coordinator.data is None:
            return {}
        summary = self.coordinator.data.get("summary", {})
        window_count = summary.get("window_count")
        shading_count = summary.get("shading_count")
        last_calculation = summary.get("calculation_time")

        return {
            "window_count": window_count if isinstance(window_count, (int, float)) else None,
            "shading_count": shading_count if isinstance(shading_count, (int, float)) else None,
            "last_calculation": last_calculation if isinstance(last_calculation, str) else None,
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
        if self.coordinator.data is None:
            return None
        value = self.coordinator.data.get(self._window_id, {}).get("power_total")
        return round(value, 1) if isinstance(value, (int, float)) else None

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if self.coordinator.data is None:
            return {}
        window_data = self.coordinator.data.get(self._window_id, {})
        power_direct = window_data.get("power_direct", 0)
        power_diffuse = window_data.get("power_diffuse", 0)
        area_m2 = window_data.get("area_m2")

        return {
            "power_direct": round(power_direct, 1) if isinstance(power_direct, (int, float)) else 0,
            "power_diffuse": round(power_diffuse, 1) if isinstance(power_diffuse, (int, float)) else 0,
            "area_m2": area_m2 if isinstance(area_m2, (int, float)) else None,
        }
