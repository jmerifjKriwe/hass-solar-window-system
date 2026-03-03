"""Coordinator for solar energy calculations."""

import logging
import math
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_WINDOWS,
    CONF_GROUPS,
    CONF_GLOBAL,
    DEFAULT_UPDATE_INTERVAL,
    CONF_SENSORS,
    CONF_THRESHOLDS,
)

_LOGGER = logging.getLogger(__name__)


class SolarCalculationCoordinator(DataUpdateCoordinator):
    """Coordinator to manage solar energy calculations."""

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            config: Configuration dictionary containing windows, groups, sensors, thresholds
        """
        super().__init__(
            hass,
            _LOGGER,
            name="Solar Window System",
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL),
        )

        self.hass = hass
        self.config = config

        # Extract windows and groups from config
        self.windows = config.get(CONF_WINDOWS, {})
        self.groups = config.get(CONF_GROUPS, {})

        # Extract global config
        self.global_config = config.get(CONF_GLOBAL, {})

        # Extract sensors and thresholds from global_config
        self.sensors = self.global_config.get(CONF_SENSORS, {})
        self.thresholds = self.global_config.get(CONF_THRESHOLDS, {})

    def _sun_is_visible(self, elevation: float, azimuth: float, window: dict) -> bool:
        """Check if the sun is visible through a window.

        Args:
            elevation: Sun elevation angle in degrees (0 = horizon, 90 = zenith)
            azimuth: Sun azimuth angle in degrees (0 = North, 90 = East, 180 = South, 270 = West)
            window: Window configuration dictionary

        Returns:
            True if sun is visible, False otherwise
        """
        # Check if sun is above horizon
        if elevation <= 0:
            return False

        # Extract geometry and properties from window dict
        geometry = window.get("geometry", {})
        properties = window.get("properties", {})

        # Check azimuth range
        az_start = geometry.get("visible_azimuth_start", 0)
        az_end = geometry.get("visible_azimuth_end", 360)

        if not (az_start <= azimuth <= az_end):
            return False

        # Check shading (roof overhangs, balconies, etc.)
        shading_depth = properties.get("shading_depth", 0)
        if shading_depth > 0:
            window_recess = properties.get("window_recess", 0)
            # Calculate shade angle: angle at which shading blocks the sun
            # The +1 prevents division by zero
            shade_angle = math.degrees(math.atan2(shading_depth, window_recess + 1))
            if elevation < shade_angle:
                return False

        return True

    async def _async_update(self) -> dict:
        """Update solar energy calculations.

        Returns:
            Dictionary with calculation results (placeholder for now)
        """
        # Placeholder - will implement in later tasks
        return {}
