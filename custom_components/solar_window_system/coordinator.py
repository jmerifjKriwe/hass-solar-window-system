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
    DEFAULT_G_VALUE,
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
            # atan2(window_recess, shading_depth) gives elevation angle from horizontal
            # The +1 prevents division by zero
            shade_angle = math.degrees(math.atan2(window_recess + 1, shading_depth))
            if elevation < shade_angle:
                return False

        return True

    async def _safe_get_sensor(self, entity_id: str, default=None) -> float | None:
        """Safely get sensor state value with graceful degradation.

        Args:
            entity_id: Home Assistant entity ID (e.g., "sensor.temperature")
            default: Default value to return if sensor is unavailable/invalid

        Returns:
            Float value of sensor state, or default if sensor is unavailable/unknown/invalid
        """
        # Get the state from Home Assistant
        state = self.hass.states.get(entity_id)

        # Check if state exists and is not in a special state
        if state is None or state.state in ["unknown", "unavailable", None]:
            return default

        # Try to convert to float
        try:
            return float(state.state)
        except (ValueError, AttributeError, KeyError):
            # ValueError: state is not numeric
            # AttributeError: state object is malformed
            # KeyError: state.attributes is missing (if we ever access them)
            return default

    def _estimate_diffuse(
        self, irradiance_total: float, elevation: float, weather_condition: str = None
    ) -> float:
        """Estimate diffuse radiation from total irradiance based on weather conditions.

        Models the ratio of diffuse to total solar radiation based on:
        - Sun elevation angle (lower sun = more diffuse due to atmospheric scattering)
        - Weather conditions (clouds increase diffuse fraction)

        Args:
            irradiance_total: Total solar irradiance in W/m²
            elevation: Sun elevation angle in degrees (0 = horizon, 90 = zenith)
            weather_condition: Optional weather condition string (e.g., "sunny", "cloudy", "rainy")

        Returns:
            Estimated diffuse radiation in W/m²
        """
        # Base model: 20% at zenith (90°) to 50% at horizon (0°)
        # This models increased atmospheric scattering at lower sun angles
        base_diffuse_ratio = 0.2 + (0.3 * (1 - elevation / 90))

        # Adjust for weather conditions
        if weather_condition:
            # Normalize to lowercase for comparison
            weather = weather_condition.lower()

            # Overcast conditions: mostly diffuse radiation
            if weather in ["cloudy", "overcast", "foggy"]:
                base_diffuse_ratio = 0.8
            # Partly cloudy conditions: mix of direct and diffuse
            elif weather in ["partlycloudy", "mostlycloudy"]:
                base_diffuse_ratio = 0.5
            # Clear conditions: use base ratio (already calculated)
            # "sunny", "clear", "" keep the base ratio

        # Clamp ratio to prevent extreme values (10% to 90%)
        base_diffuse_ratio = max(0.1, min(0.9, base_diffuse_ratio))

        # Calculate diffuse radiation
        return irradiance_total * base_diffuse_ratio

    def _get_zero_results(self) -> dict:
        """Get zero energy results for all windows.

        Returns:
            Dictionary with all windows having direct=0, diffuse=0, combined=0
        """
        results = {}
        for window_id in self.windows:
            results[window_id] = {
                "direct": 0,
                "diffuse": 0,
                "combined": 0,
            }
        return results

    def _calculate_direct_energy(
        self,
        irradiance_direct: float,
        elevation: float,
        azimuth: float,
        window: dict
    ) -> float:
        """Calculate direct solar energy through a window.

        Args:
            irradiance_direct: Direct solar irradiance in W/m²
            elevation: Sun elevation angle in degrees
            azimuth: Sun azimuth angle in degrees
            window: Window configuration dictionary

        Returns:
            Direct energy in watts
        """
        geometry = window.get("geometry", {})
        properties = window.get("properties", {})

        # Get dimensions and properties
        width = geometry.get("width", 0)
        height = geometry.get("height", 0)
        frame_width = properties.get("frame_width", 0)
        g_value = properties.get("g_value", DEFAULT_G_VALUE)
        window_azimuth = geometry.get("azimuth", 180)

        # Calculate effective area (subtract frame on all sides)
        # Area is in cm², convert to m² (divide by 10000)
        effective_area_m2 = ((width - 2 * frame_width) * (height - 2 * frame_width)) / 10000

        # Calculate incidence factor based on azimuth difference
        # cos(0) = 1 (sun directly facing window), cos(90) = 0 (sun from side)
        azimuth_diff = abs(azimuth - window_azimuth)
        incidence_factor = max(0, math.cos(math.radians(azimuth_diff)))

        # Calculate direct energy
        return irradiance_direct * effective_area_m2 * incidence_factor * g_value

    def _calculate_diffuse_energy(
        self,
        irradiance_diffuse: float,
        window: dict
    ) -> float:
        """Calculate diffuse solar energy through a window.

        Args:
            irradiance_diffuse: Diffuse solar irradiance in W/m²
            window: Window configuration dictionary

        Returns:
            Diffuse energy in watts
        """
        geometry = window.get("geometry", {})
        properties = window.get("properties", {})

        # Get dimensions and properties
        width = geometry.get("width", 0)
        height = geometry.get("height", 0)
        frame_width = properties.get("frame_width", 0)
        g_value = properties.get("g_value", DEFAULT_G_VALUE)

        # Calculate effective area (subtract frame on all sides)
        # Area is in cm², convert to m² (divide by 10000)
        effective_area_m2 = ((width - 2 * frame_width) * (height - 2 * frame_width)) / 10000

        # Calculate diffuse energy (no incidence factor for diffuse)
        return irradiance_diffuse * effective_area_m2 * g_value

    async def _async_update(self) -> dict:
        """Update solar energy calculations.

        Returns:
            Dictionary with calculation results for each window
        """
        # Get sun state
        sun_state = self.hass.states.get("sun.sun")

        # Check if it's night
        if sun_state is None or sun_state.state == "below_horizon":
            return self._get_zero_results()

        # Get sun position from attributes
        sun_attrs = sun_state.attributes
        elevation = sun_attrs.get("elevation", 0)
        azimuth = sun_attrs.get("azimuth", 180)

        # Get total irradiance from sensor
        irradiance_total = await self._safe_get_sensor(
            self.sensors.get("irradiance_sensor"),
            default=0
        )

        # If no irradiance data, return zero results
        if irradiance_total is None or irradiance_total == 0:
            return self._get_zero_results()

        # Get or estimate diffuse irradiance
        # Check if diffuse sensor exists
        diffuse_sensor = self.sensors.get("diffuse_irradiance_sensor")
        if diffuse_sensor:
            irradiance_diffuse = await self._safe_get_sensor(diffuse_sensor, default=0)
            # Explicit None check for type safety
            if irradiance_diffuse is None:
                irradiance_diffuse = 0.0
        else:
            # Estimate diffuse from total
            irradiance_diffuse = self._estimate_diffuse(irradiance_total, elevation)

        # Calculate direct irradiance
        irradiance_direct = irradiance_total - irradiance_diffuse

        # Ensure non-negative values
        irradiance_direct = max(0, irradiance_direct)
        irradiance_diffuse = max(0, irradiance_diffuse)

        # Calculate energy for each window
        results = {}
        for window_id, window in self.windows.items():
            # Check if sun is visible through this window
            if self._sun_is_visible(elevation, azimuth, window):
                # Calculate both direct and diffuse energy
                direct = self._calculate_direct_energy(
                    irradiance_direct, elevation, azimuth, window
                )
                diffuse = self._calculate_diffuse_energy(irradiance_diffuse, window)
            else:
                # Sun not visible, only diffuse energy
                direct = 0
                diffuse = self._calculate_diffuse_energy(irradiance_diffuse, window)

            # Calculate combined energy
            combined = direct + diffuse

            # Store results
            results[window_id] = {
                "direct": direct,
                "diffuse": diffuse,
                "combined": combined,
            }

        return results
