"""Coordinator for solar energy calculations."""

import logging
import math
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_AZIMUTH,
    CONF_FRAME_WIDTH,
    CONF_G_VALUE,
    CONF_GEOMETRY,
    CONF_GROUP_ID,
    CONF_GROUPS,
    CONF_HEIGHT,
    CONF_IRRADIANCE_SENSOR,
    CONF_OVERRIDES,
    CONF_PROPERTIES,
    CONF_SCENARIO_FORECAST,
    CONF_SCENARIO_INDOOR,
    CONF_SCENARIO_OUTDOOR,
    CONF_SENSORS,
    CONF_SHADING_DEPTH,
    CONF_TEMP_INDOOR,
    CONF_TEMP_OUTDOOR,
    CONF_THRESHOLD_FORECAST,
    CONF_THRESHOLD_INDOOR,
    CONF_THRESHOLD_OUTDOOR,
    CONF_THRESHOLD_RADIATION,
    CONF_USE_IRRADIANCE_DIFFUSE,
    CONF_USE_TEMP_INDOOR,
    CONF_USE_TEMP_OUTDOOR,
    CONF_USE_WEATHER_CONDITION,
    CONF_USE_WEATHER_WARNING,
    CONF_WEATHER_CONDITION,
    CONF_WEATHER_WARNING,
    CONF_WIDTH,
    CONF_WINDOW_RECESS,
    CONF_WINDOWS,
    DEFAULT_FORECAST_HIGH,
    DEFAULT_FRAME_WIDTH,
    DEFAULT_G_VALUE,
    DEFAULT_INSIDE_TEMP,
    DEFAULT_OUTSIDE_TEMP,
    DEFAULT_SHADING_DEPTH,
    DEFAULT_SOLAR_ENERGY,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_WINDOW_RECESS,
    DOMAIN,
    LEVEL_GLOBAL,
    LEVEL_GROUP,
    LEVEL_WINDOW,
)

_LOGGER = logging.getLogger(__name__)

# Default values for inheritance
DEFAULT_THRESHOLDS = {
    CONF_THRESHOLD_INDOOR: DEFAULT_INSIDE_TEMP,
    CONF_THRESHOLD_OUTDOOR: DEFAULT_OUTSIDE_TEMP,
    CONF_THRESHOLD_FORECAST: DEFAULT_FORECAST_HIGH,
    CONF_THRESHOLD_RADIATION: DEFAULT_SOLAR_ENERGY,
}

DEFAULT_SCENARIOS = {
    CONF_SCENARIO_INDOOR: True,
    CONF_SCENARIO_OUTDOOR: True,
    CONF_SCENARIO_FORECAST: True,
}

DEFAULT_PROPERTIES = {
    CONF_G_VALUE: DEFAULT_G_VALUE,
    CONF_FRAME_WIDTH: DEFAULT_FRAME_WIDTH,
    CONF_WINDOW_RECESS: DEFAULT_WINDOW_RECESS,
    CONF_SHADING_DEPTH: DEFAULT_SHADING_DEPTH,
}


class SolarCalculationCoordinator(DataUpdateCoordinator):
    """Coordinator to manage solar energy calculations with inheritance."""

    def __init__(
        self,
        hass: HomeAssistant,
        config: dict,
        subentries: dict,
        overrides: dict,
        config_entry: ConfigEntry | None = None,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            config: Global configuration from config entry
            subentries: Subentries data (windows and groups)
            overrides: Override values stored in persistent storage
            config_entry: The config entry this coordinator belongs to
        """
        super().__init__(
            hass,
            _LOGGER,
            name="Solar Window System",
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL),
            config_entry=config_entry,
        )

        self.hass = hass
        self.config = config
        self._subentries = subentries or {}
        self._overrides = overrides or {}

        # Extract global config
        self.global_sensors = config.get(CONF_SENSORS, {})
        self.global_properties = config.get(CONF_PROPERTIES, {})

        # Extract windows and groups from subentries
        self.windows = self._extract_windows()
        self.groups = self._extract_groups()

        # Store reference to storage (set during async_setup_entry)
        self._store: Store | None = None

        # Error tracking for debug entities
        self._config_errors: list[str] = []
        self._runtime_errors: list[str] = []

    def _extract_windows(self) -> dict:
        """Extract windows from subentries data."""
        windows = {}
        if isinstance(self._subentries, dict):
            for key, data in self._subentries.items():
                if isinstance(data, dict) and data.get("type") == "window":
                    windows[key] = data
        return windows

    def _extract_groups(self) -> dict:
        """Extract groups from subentries data."""
        groups = {}
        if isinstance(self._subentries, dict):
            for key, data in self._subentries.items():
                if isinstance(data, dict) and data.get("type") == "group":
                    groups[key] = data
        return groups

    def set_store(self, store: Store) -> None:
        """Set the storage reference for saving overrides."""
        self._store = store

    def get_effective_value(self, level: str, entity_id: str, property_name: str) -> Any:
        """Get effective value with inheritance: Window -> Group -> Global.

        Args:
            level: One of LEVEL_WINDOW, LEVEL_GROUP, LEVEL_GLOBAL
            entity_id: ID of the window, group, or "global"
            property_name: Name of the property to retrieve

        Returns:
            The effective value considering overrides and inheritance
        """
        # 1. Check local override for this specific entity
        if level in self._overrides and entity_id in self._overrides[level]:
            entity_overrides = self._overrides[level][entity_id]
            if property_name in entity_overrides:
                return entity_overrides[property_name]

        # 2. For windows, check group values if window belongs to a group
        if level == LEVEL_WINDOW and entity_id in self.windows:
            window = self.windows[entity_id]
            group_id = window.get(CONF_GROUP_ID)
            if group_id and group_id in self.groups:
                # Check group overrides first
                if LEVEL_GROUP in self._overrides and group_id in self._overrides[LEVEL_GROUP]:
                    group_overrides = self._overrides[LEVEL_GROUP][group_id]
                    if property_name in group_overrides:
                        return group_overrides[property_name]
                # Then check group static config
                group = self.groups[group_id]
                if CONF_PROPERTIES in group and property_name in group[CONF_PROPERTIES]:
                    return group[CONF_PROPERTIES][property_name]

        # 3. For windows/groups, check global static config
        if property_name.startswith("threshold_"):
            if property_name in DEFAULT_THRESHOLDS:
                return DEFAULT_THRESHOLDS[property_name]
        elif property_name.startswith("scenario_"):
            if property_name in DEFAULT_SCENARIOS:
                return DEFAULT_SCENARIOS[property_name]
        elif property_name in [
            CONF_G_VALUE,
            CONF_FRAME_WIDTH,
            CONF_WINDOW_RECESS,
            CONF_SHADING_DEPTH,
        ]:
            if property_name in self.global_properties:
                return self.global_properties[property_name]
            if property_name in DEFAULT_PROPERTIES:
                return DEFAULT_PROPERTIES[property_name]

        # Final fallback
        return None

    async def set_override(
        self, level: str, entity_id: str, property_name: str, value: Any
    ) -> None:
        """Set an override value for a specific entity.

        Args:
            level: One of LEVEL_WINDOW, LEVEL_GROUP, LEVEL_GLOBAL
            entity_id: ID of the window, group, or "global"
            property_name: Name of the property to override
            value: New value to set
        """
        if level not in self._overrides:
            self._overrides[level] = {}
        if entity_id not in self._overrides[level]:
            self._overrides[level][entity_id] = {}

        self._overrides[level][entity_id][property_name] = value

        # Persist to storage
        if self._store:
            await self._store.async_save({CONF_OVERRIDES: self._overrides})

    async def clear_overrides(self, level: str, entity_id: str) -> None:
        """Clear all overrides for a specific entity.

        Args:
            level: One of LEVEL_WINDOW, LEVEL_GROUP, LEVEL_GLOBAL
            entity_id: ID of the window, group, or "global"
        """
        if level in self._overrides and entity_id in self._overrides[level]:
            del self._overrides[level][entity_id]
            # Persist to storage
            if self._store:
                await self._store.async_save({CONF_OVERRIDES: self._overrides})

    def _get_window_property(self, window_id: str, property_name: str) -> Any:
        """Get window property with full inheritance chain."""
        window = self.windows.get(window_id, {})

        # 1. Check window properties from config
        if CONF_PROPERTIES in window and property_name in window[CONF_PROPERTIES]:
            return window[CONF_PROPERTIES][property_name]

        # 2. Check group if window belongs to one
        group_id = window.get(CONF_GROUP_ID)
        if group_id and group_id in self.groups:
            group = self.groups[group_id]
            if CONF_PROPERTIES in group and property_name in group[CONF_PROPERTIES]:
                return group[CONF_PROPERTIES][property_name]

        # 3. Fall back to global
        return self.global_properties.get(property_name, DEFAULT_PROPERTIES.get(property_name))

    def _get_window_geometry(self, window_id: str) -> dict:
        """Get window geometry."""
        window = self.windows.get(window_id, {})
        return window.get(CONF_GEOMETRY, {})

    def _sun_is_visible(self, elevation: float, azimuth: float, window_id: str) -> bool:
        """Check if the sun is visible through a window.

        Args:
            elevation: Sun elevation angle in degrees (0 = horizon, 90 = zenith)
            azimuth: Sun azimuth angle in degrees (0 = North, 90 = East, 180 = South, 270 = West)
            window_id: Window identifier string

        Returns:
            True if sun is visible, False otherwise
        """
        # Check if sun is above horizon
        if elevation <= 0:
            return False

        # Get window configuration
        window = self.windows.get(window_id, {})

        # Extract geometry and properties from window dict
        geometry = window.get(CONF_GEOMETRY, {})
        _ = window.get(CONF_PROPERTIES, {})  # Properties used by _get_window_property

        # Check azimuth range
        az_start = geometry.get("visible_azimuth_start", 0)
        az_end = geometry.get("visible_azimuth_end", 360)

        if not (az_start <= azimuth <= az_end):
            return False

        # Check shading (roof overhangs, balconies, etc.) using inherited properties
        shading_depth = self._get_window_property(window_id, CONF_SHADING_DEPTH)
        if shading_depth > 0:
            window_recess = self._get_window_property(window_id, CONF_WINDOW_RECESS)
            # Calculate shade angle: angle at which shading blocks the sun
            # atan2(window_recess, shading_depth) gives elevation angle from horizontal
            # The +1 prevents division by zero
            shade_angle = math.degrees(math.atan2(window_recess + 1, shading_depth))
            if elevation < shade_angle:
                return False

        return True

    async def _safe_get_sensor(
        self, entity_id: str, default=None, error_context: str | None = None
    ) -> float | None:
        """Safely get sensor state value with graceful degradation.

        Args:
            entity_id: Home Assistant entity ID (e.g., "sensor.temperature")
            default: Default value to return if sensor is unavailable/invalid
            error_context: Optional context for error messages (e.g., window name)

        Returns:
            Float value of sensor state, or default if sensor is unavailable/unknown/invalid
        """
        # Check if entity_id is None before querying Home Assistant
        if entity_id is None:
            return default

        # Get the state from Home Assistant
        state = self.hass.states.get(entity_id)

        # Check if state exists and is not in a special state
        if state is None:
            context = f" ({error_context})" if error_context else ""
            self.add_runtime_error(f"Sensor '{entity_id}' nicht gefunden{context}")
            return default

        if state.state in ["unknown", "unavailable", None]:
            context = f" ({error_context})" if error_context else ""
            self.add_runtime_error(f"Sensor '{entity_id}': Status '{state.state}'{context}")
            return default

        # Try to convert to float
        try:
            return float(state.state)
        except ValueError:
            context = f" ({error_context})" if error_context else ""
            self.add_runtime_error(
                f"Sensor '{entity_id}': Ungültiger Wert '{state.state}'{context}"
            )
            return default
        except AttributeError:
            return default
        except KeyError:
            return default

    def _estimate_diffuse(
        self,
        irradiance_total: float,
        elevation: float,
        weather_condition: str | None = None,
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
        """Get zero energy results for all windows, groups, and global.

        Returns:
            Dictionary with all windows, groups, and global having direct=0, diffuse=0, combined=0
        """
        results = {}
        # Add zero results for all windows
        for window_id in self.windows:
            results[window_id] = {
                "direct": 0,
                "diffuse": 0,
                "combined": 0,
            }
        # Add zero results for all groups
        for group_id in self.groups:
            results[f"group_{group_id}"] = {
                "direct": 0,
                "diffuse": 0,
                "combined": 0,
            }
        # Add zero result for global
        results["global"] = {
            "direct": 0,
            "diffuse": 0,
            "combined": 0,
        }
        return results

    def _calculate_direct_energy(
        self, irradiance_direct: float, elevation: float, azimuth: float, window: dict
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
        window_tilt = geometry.get("tilt", 90)  # Default 90° = vertical

        # Calculate effective area (subtract frame on all sides)
        # Area is in cm², convert to m² (divide by 10000)
        effective_area_m2 = ((width - 2 * frame_width) * (height - 2 * frame_width)) / 10000

        # Calculate incidence factor considering tilt angle
        # Formula: cos(θ) = sin(α)*cos(β) + cos(α)*sin(β)*cos(γ-δ)
        # Where: α=elevation, β=tilt, γ=sun_azimuth, δ=window_azimuth
        alpha = math.radians(elevation)
        beta = math.radians(window_tilt)
        azimuth_diff = math.radians(azimuth - window_azimuth)

        incidence_factor = math.sin(alpha) * math.cos(beta) + math.cos(alpha) * math.sin(
            beta
        ) * math.cos(azimuth_diff)
        incidence_factor = max(0, incidence_factor)  # No negative values

        # Calculate direct energy
        return irradiance_direct * effective_area_m2 * incidence_factor * g_value

    def _calculate_diffuse_energy(self, irradiance_diffuse: float, window: dict) -> float:
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
        window_tilt = geometry.get("tilt", 90)  # Default 90° = vertical

        # Calculate effective area (subtract frame on all sides)
        # Area is in cm², convert to m² (divide by 10000)
        effective_area_m2 = ((width - 2 * frame_width) * (height - 2 * frame_width)) / 10000

        # Calculate diffuse incidence factor based on tilt
        # Horizontal (0°) sees full sky, vertical (90°) sees half
        # Formula: (1 + cos(β)) / 2 where β = tilt angle
        incidence_factor = (1 + math.cos(math.radians(window_tilt))) / 2

        # Calculate diffuse energy
        return irradiance_diffuse * effective_area_m2 * incidence_factor * g_value

    def _aggregate_group(self, window_ids: list, results: dict) -> dict:
        """Aggregate energy values for a group of windows.

        Args:
            window_ids: List of window IDs to aggregate
            results: Dictionary containing calculation results for each window

        Returns:
            Dictionary with aggregated direct, diffuse, and combined energy
        """
        aggregated = {"direct": 0, "diffuse": 0, "combined": 0}
        for window_id in window_ids:
            if window_id in results:
                window_data = results[window_id]
                aggregated["direct"] += window_data.get("direct", 0)
                aggregated["diffuse"] += window_data.get("diffuse", 0)
                aggregated["combined"] += window_data.get("combined", 0)
        return aggregated

    def _aggregate_all(self, results: dict) -> dict:
        """Aggregate energy values for all windows (global aggregation).

        Args:
            results: Dictionary containing calculation results for windows and groups

        Returns:
            Dictionary with aggregated direct, diffuse, and combined energy
        """
        aggregated = {"direct": 0, "diffuse": 0, "combined": 0}
        for key, value in results.items():
            # Skip group_* and global keys (only sum actual windows)
            if not key.startswith("group_") and key != "global":
                aggregated["direct"] += value.get("direct", 0)
                aggregated["diffuse"] += value.get("diffuse", 0)
                aggregated["combined"] += value.get("combined", 0)
        return aggregated

    async def _async_update_data(self) -> dict:
        """Update solar energy calculations.

        Returns:
            Dictionary with calculation results for each window
        """
        # Clear runtime errors from previous cycle
        self.clear_runtime_errors()

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
            self.global_sensors.get("irradiance_sensor"), default=0
        )

        # If no irradiance data, return zero results
        if irradiance_total is None or irradiance_total == 0:
            return self._get_zero_results()

        # Get or estimate diffuse irradiance
        # Check if diffuse sensor is enabled and exists
        diffuse_sensor = self.global_sensors.get("irradiance_diffuse_sensor")
        if self.config.get(CONF_USE_IRRADIANCE_DIFFUSE) and diffuse_sensor:
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
        shading_results = {}
        for window_id, window in self.windows.items():
            # Check if sun is visible through this window
            if self._sun_is_visible(elevation, azimuth, window_id):
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

            # Calculate shading recommendation
            shading_results[window_id] = await self._should_shade(window_id, combined)

        # Calculate group aggregations
        for group_id, group in self.groups.items():
            group_result = self._aggregate_group(group.get("windows", []), results)
            results[f"group_{group_id}"] = group_result
            # Group shading is ON if any window recommends shading
            shading_results[f"group_{group_id}"] = any(
                shading_results.get(wid, False) for wid in group.get("windows", [])
            )

        # Calculate global aggregation
        global_result = self._aggregate_all(results)
        results["global"] = global_result
        # Global shading is ON if any window recommends shading
        shading_results["global"] = any(shading_results.get(wid, False) for wid in self.windows)

        # Merge energy results with shading results
        for key in results:
            results[key]["shading_recommended"] = shading_results.get(key, False)

        return results

    async def _should_shade(self, window_id: str, combined_energy: float) -> bool:
        """Determine if shading is recommended for a window.

        Args:
            window_id: ID of the window to check
            combined_energy: Combined solar energy in Watts

        Returns:
            True if shading is recommended, False otherwise
        """
        # 1. Check weather warning (master override - disables all recommendations)
        weather_warning = self.global_sensors.get("weather_warning")
        if self.config.get(CONF_USE_WEATHER_WARNING) and weather_warning:
            warning_state = await self._safe_get_sensor(weather_warning, default="off")
            if warning_state == "on":
                return False

        triggers = []

        # 2. Szenario Indoor
        if self.get_effective_value(LEVEL_WINDOW, window_id, CONF_SCENARIO_INDOOR):
            indoor_temp = await self._get_indoor_temp(window_id)
            threshold = self.get_effective_value(LEVEL_WINDOW, window_id, CONF_THRESHOLD_INDOOR)
            if indoor_temp and indoor_temp > threshold:
                triggers.append("indoor_temp")

        # 3. Szenario Outdoor
        if self.get_effective_value(LEVEL_WINDOW, window_id, CONF_SCENARIO_OUTDOOR):
            outdoor_temp = None
            if self.config.get(CONF_USE_TEMP_OUTDOOR):
                outdoor_temp = await self._safe_get_sensor(
                    self.global_sensors.get("temp_outdoor"), default=None
                )
            threshold = self.get_effective_value(LEVEL_WINDOW, window_id, CONF_THRESHOLD_OUTDOOR)
            if outdoor_temp and outdoor_temp > threshold:
                triggers.append("outdoor_temp")

        # 4. Szenario Forecast
        if self.get_effective_value(LEVEL_WINDOW, window_id, CONF_SCENARIO_FORECAST):
            forecast_high = await self._get_forecast_high()
            threshold = self.get_effective_value(LEVEL_WINDOW, window_id, CONF_THRESHOLD_FORECAST)
            indoor_temp = await self._get_indoor_temp(window_id)
            if forecast_high and indoor_temp:
                if forecast_high > threshold and indoor_temp > threshold - 2:
                    triggers.append("forecast")

        # 5. Solarenergie-Check (zusätzlich zu Temp-Triggers)
        rad_threshold = self.get_effective_value(LEVEL_WINDOW, window_id, CONF_THRESHOLD_RADIATION)
        if combined_energy > rad_threshold and triggers:
            return True

        return False

    def _get_azimuth(self, window_id: str) -> int | None:
        """Get azimuth for a window with inheritance: Window -> Group -> None.

        Args:
            window_id: The ID of the window to get azimuth for.

        Returns:
            Azimuth in degrees (0-360) or None if not found anywhere.
            Logs debug error if neither window nor group has azimuth.
        """
        window = self.windows.get(window_id, {})

        # Priority 1: Window direct azimuth
        window_geometry = window.get(CONF_GEOMETRY, {})
        if CONF_AZIMUTH in window_geometry:
            return window_geometry[CONF_AZIMUTH]

        # Priority 2: Group azimuth
        group_id = window.get(CONF_GROUP_ID)
        if group_id and group_id in self.groups:
            group = self.groups[group_id]
            if CONF_AZIMUTH in group:
                return group[CONF_AZIMUTH]

        # Priority 3: None - log debug error
        _LOGGER.debug("Window '%s' has neither direct nor inherited orientation", window_id)
        return None

    async def _get_indoor_temp(self, window_id: str) -> float | None:
        """Get indoor temperature for window with inheritance: Window -> Group -> Global."""
        window = self.windows.get(window_id, {})

        # Priority 1: Window direct sensor
        window_sensors = window.get(CONF_SENSORS, {})
        if CONF_TEMP_INDOOR in window_sensors:
            return await self._safe_get_sensor(window_sensors[CONF_TEMP_INDOOR], default=None)

        # Priority 2: Group sensor
        group_id = window.get(CONF_GROUP_ID)

        # Try group sensor first if window belongs to a group
        if group_id and group_id in self.groups:
            group = self.groups[group_id]
            group_sensor = group.get(CONF_SENSORS, {}).get(CONF_TEMP_INDOOR)
            if group_sensor:
                return await self._safe_get_sensor(group_sensor, default=None)

        # Priority 3: Global sensor (if configured)
        global_sensor = self.global_sensors.get(CONF_TEMP_INDOOR)
        if global_sensor:
            return await self._safe_get_sensor(global_sensor, default=None)

        # Priority 4: None - log debug error
        _LOGGER.debug(
            "Window '%s': no indoor temperature sensor in window, group, or Solar Window System",
            window_id,
        )
        return None

    async def _get_forecast_high(self) -> float | None:
        """Get forecasted high temperature for today."""
        # Check if weather condition sensor is enabled
        if not self.config.get(CONF_USE_WEATHER_CONDITION):
            return None

        # Try to get forecast from weather entity
        try:
            # Call weather service to get forecast
            response = await self.hass.services.async_call(
                "weather",
                "get_forecasts",
                {
                    "entity_id": self.global_sensors.get(CONF_WEATHER_CONDITION),
                    "type": "daily",
                },
                blocking=True,
                return_response=True,
            )
            if response:
                # Extract high temperature from forecast
                forecast_data = response.get("forecast", [])
                if isinstance(forecast_data, list) and forecast_data:
                    first_forecast = forecast_data[0]
                    if isinstance(first_forecast, dict):
                        temp = first_forecast.get("temperature")
                        if isinstance(temp, (int, float)):
                            return float(temp)
        except Exception:
            pass

        return None

    def validate_configuration(self) -> list[str]:
        """Validate configuration and return list of error messages.

        Returns:
            List of human-readable error messages for config issues.
        """
        errors: list[str] = []

        # Validate each window
        for window_id, window in self.windows.items():
            window_name = window.get("name", window_id)
            geometry = window.get(CONF_GEOMETRY, {})

            # Check for missing azimuth
            if CONF_AZIMUTH not in geometry:
                # Check if group has azimuth
                group_id = window.get(CONF_GROUP_ID)
                has_group_azimuth = False
                if group_id and group_id in self.groups:
                    group = self.groups[group_id]
                    if CONF_AZIMUTH in group:
                        has_group_azimuth = True
                if not has_group_azimuth:
                    errors.append(f"Fenster '{window_name}': Keine Azimuth definiert")

            # Check for invalid dimensions
            width = geometry.get(CONF_WIDTH, 0)
            height = geometry.get(CONF_HEIGHT, 0)
            if width <= 0:
                errors.append(f"Fenster '{window_name}': Breite ungültig ({width})")
            if height <= 0:
                errors.append(f"Fenster '{window_name}': Höhe ungültig ({height})")

            # Check window sensors exist
            window_sensors = window.get(CONF_SENSORS, {})
            temp_indoor = window_sensors.get(CONF_TEMP_INDOOR)
            if temp_indoor and not self._entity_exists(temp_indoor):
                errors.append(f"Fenster '{window_name}': Sensor '{temp_indoor}' nicht gefunden")

        # Validate global sensors
        irradiance_sensor = self.global_sensors.get(CONF_IRRADIANCE_SENSOR)
        if irradiance_sensor and not self._entity_exists(irradiance_sensor):
            errors.append(f"Global: Sensor '{irradiance_sensor}' nicht gefunden")

        temp_outdoor = self.global_sensors.get(CONF_TEMP_OUTDOOR)
        if temp_outdoor and not self._entity_exists(temp_outdoor):
            errors.append(f"Global: Sensor '{temp_outdoor}' nicht gefunden")

        weather_condition = self.global_sensors.get(CONF_WEATHER_CONDITION)
        if weather_condition and not self._entity_exists(weather_condition):
            errors.append(f"Global: Wetter '{weather_condition}' nicht gefunden")

        self._config_errors = errors
        return errors

    def _entity_exists(self, entity_id: str) -> bool:
        """Check if an entity exists in Home Assistant."""
        if entity_id is None:
            return False
        return self.hass.states.get(entity_id) is not None

    def get_config_errors(self) -> list[str]:
        """Return cached configuration errors."""
        return self._config_errors

    def get_runtime_errors(self) -> list[str]:
        """Return cached runtime errors from last update cycle."""
        return self._runtime_errors

    def add_runtime_error(self, error: str) -> None:
        """Add a runtime error to the tracking list."""
        if error not in self._runtime_errors:
            self._runtime_errors.append(error)

    def clear_runtime_errors(self) -> None:
        """Clear runtime errors before new update cycle."""
        self._runtime_errors = []
