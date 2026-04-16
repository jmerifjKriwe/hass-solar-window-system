"""Diagnostic sensors for Solar Window System debug information."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEBUG_TYPE_CONFIG, DEBUG_TYPE_RUNTIME, DOMAIN

if TYPE_CHECKING:
    from .coordinator import SolarCalculationCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up diagnostic sensor entities from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    # Create both debug sensors
    entities = [
        ConfigDebugSensor(coordinator),
        RuntimeDebugSensor(coordinator),
    ]

    async_add_entities(entities)


class DebugSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for debug sensors."""

    coordinator: SolarCalculationCoordinator
    _debug_type: str

    def __init__(
        self,
        coordinator: SolarCalculationCoordinator,
        debug_type: str,
    ) -> None:
        """Initialize the debug sensor.

        Args:
            coordinator: DataUpdateCoordinator instance
            debug_type: One of DEBUG_TYPE_CONFIG or DEBUG_TYPE_RUNTIME
        """
        super().__init__(coordinator)
        self._debug_type = debug_type

    @property
    def unique_id(self) -> str:
        """Return a unique ID for this sensor."""
        return f"{DOMAIN}_debug_{self._debug_type}"

    @property
    def entity_category(self):
        """Return the entity category."""
        return EntityCategory.DIAGNOSTIC

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, "global")},
            name="Solar Window System Global",
            manufacturer="Solar Window System",
        )

    def _get_error_count_text(self, count: int) -> str:
        """Return formatted error count text."""
        if count == 0:
            return "OK"
        elif count == 1:
            return "1 Fehler"
        else:
            return f"{count} Fehler"


class ConfigDebugSensor(DebugSensorBase):
    """Sensor showing configuration errors."""

    def __init__(self, coordinator: SolarCalculationCoordinator) -> None:
        """Initialize the config debug sensor."""
        super().__init__(coordinator, DEBUG_TYPE_CONFIG)

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Solar Window System Debug Config"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        errors = self.coordinator.get_config_errors()
        return self._get_error_count_text(len(errors))

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        errors = self.coordinator.get_config_errors()

        attributes: dict = {
            "last_check": datetime.now().isoformat(),
            "error_count": len(errors),
        }

        if errors:
            attributes["errors"] = errors

        return attributes


class RuntimeDebugSensor(DebugSensorBase):
    """Sensor showing runtime errors from last update cycle."""

    def __init__(self, coordinator: SolarCalculationCoordinator) -> None:
        """Initialize the runtime debug sensor."""
        super().__init__(coordinator, DEBUG_TYPE_RUNTIME)

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Solar Window System Debug Runtime"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        errors = self.coordinator.get_runtime_errors()
        return self._get_error_count_text(len(errors))

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional attributes."""
        errors = self.coordinator.get_runtime_errors()

        attributes: dict = {
            "last_update": datetime.now().isoformat(),
            "error_count": len(errors),
        }

        if errors:
            attributes["errors"] = errors

        return attributes
