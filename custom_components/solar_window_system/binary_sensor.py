# /config/custom_components/solar_window_system/binary_sensor.py
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
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
    """Set up the binary sensor entities."""
    coordinator: SolarWindowDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Data should now be available after async_config_entry_first_refresh
    if coordinator.data is None:
        _LOGGER.error(
            "Coordinator data is None after initial refresh. This shouldn't happen."
        )
        return

    async_add_entities(
        SolarWindowShadingSensor(coordinator, window_id)
        for window_id in coordinator.data
        if window_id != "summary"
    )


class SolarWindowShadingSensor(SolarWindowSystemDataEntity, BinarySensorEntity):
    """Representation of a shading sensor for a single window."""

    def __init__(self, coordinator: SolarWindowDataUpdateCoordinator, window_id: str):
        """Initialize the window sensor."""
        super().__init__(coordinator)
        self._window_id = window_id

        self._attr_name = (
            f"{coordinator.data[self._window_id].get('name', window_id)} Shading"
        )
        self._attr_unique_id = f"{DOMAIN}_{window_id}_shading"
        self._attr_device_class = BinarySensorDeviceClass.OPENING

    @property
    def is_on(self) -> bool | None:
        """Return true if shading is required."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._window_id, {}).get("shade_required")

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if self.coordinator.data is None:
            return {}

        window_data = self.coordinator.data.get(self._window_id, {})
        power_total = window_data.get("power_total", 0)

        return {
            "reason": window_data.get("shade_reason"),
            "power_total_w": round(power_total, 1),
            "shading_threshold_w": round(window_data.get("effective_threshold", 0), 1),
        }
