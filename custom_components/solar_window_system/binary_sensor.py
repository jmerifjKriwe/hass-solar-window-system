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

    if coordinator.data:
        async_add_entities(
            [
                SolarWindowShadingSensor(coordinator, window_id)
                for window_id in coordinator.data
                if window_id != "summary"
            ]
        )
    else:
        _LOGGER.info("Coordinator data is None")


class SolarWindowShadingSensor(SolarWindowSystemDataEntity, BinarySensorEntity):
    """Representation of a shading sensor for a single window."""

    def __init__(self, coordinator: SolarWindowDataUpdateCoordinator, window_id: str):
        """Initialize the window sensor."""
        super().__init__(coordinator)
        self._window_id = window_id

        # Set a default name. It will be updated in the first refresh if data is available.
        self._attr_name = f"{window_id.replace('_', ' ').title()} Shading"
        self._attr_unique_id = f"{DOMAIN}_{window_id}_shading"
        self._attr_device_class = BinarySensorDeviceClass.OPENING

        # Update the name if coordinator data is available
        if coordinator.data and window_id in coordinator.data:
            self._attr_name = (
                f"{coordinator.data[self._window_id].get('name', window_id)} Shading"
            )

    @property
    def is_on(self) -> bool | None:
        """Return true if shading is required."""
        if self.coordinator.data is None:
            return None
        shade_required = self.coordinator.data.get(self._window_id, {}).get("shade_required")
        if isinstance(shade_required, bool):
            return shade_required
        return None

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if self.coordinator.data is None:
            return {}

        window_data = self.coordinator.data.get(self._window_id, {})
        power_total = window_data.get("power_total", 0)
        effective_threshold = window_data.get("effective_threshold", 0)

        if not isinstance(power_total, (int, float)):
            power_total = 0
        if not isinstance(effective_threshold, (int, float)):
            effective_threshold = 0

        return {
            "reason": window_data.get("shade_reason"),
            "power_total_w": power_total,
            "shading_threshold_w": effective_threshold,
        }
