# /config/custom_components/solar_window_system/binary_sensor.py
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_ENTRY_TYPE
from .coordinator import SolarWindowDataUpdateCoordinator
from .entity import SolarWindowSystemDataEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor entities."""
    if entry.data.get(CONF_ENTRY_TYPE) == "window":
        # For window entries, the config is directly in entry.options
        window_config = entry.options
        # The coordinator for global data is still needed
        # Assuming the global config entry ID is stored somewhere accessible, or we find it.
        # For now, let's assume the global coordinator is available via DOMAIN and its entry_id
        # This part needs careful consideration of how to access the global coordinator.
        # For now, we'll pass a dummy coordinator or find the global one.
        # Let's assume the global config entry is the first one found for simplicity for now.
        global_entry = None
        for ent in hass.config_entries.async_entries(DOMAIN):
            if ent.data.get(CONF_ENTRY_TYPE) == "global":
                global_entry = ent
                break

        if global_entry:
            coordinator: SolarWindowDataUpdateCoordinator = hass.data[DOMAIN][
                global_entry.entry_id
            ]
            async_add_entities(
                [SolarWindowShadingSensor(coordinator, entry.entry_id, window_config)]
            )
        else:
            _LOGGER.warning(
                "Global configuration entry not found. Cannot set up window binary sensor."
            )
    else:
        # This platform only handles window entries now
        return


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
        shade_required = self.coordinator.data.get(self._window_id, {}).get(
            "shade_required"
        )
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
