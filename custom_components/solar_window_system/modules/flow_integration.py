"""
Flow-based integration and configuration handling.

This module contains flow-based configuration logic, inheritance handling,
and window calculation results.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import logging
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


@dataclass
class WindowCalculationResult:
    """Result of window solar power calculation."""

    power_total: float
    power_direct: float
    power_diffuse: float
    power_direct_raw: float
    power_diffuse_raw: float
    power_total_raw: float
    shadow_factor: float
    is_visible: bool
    area_m2: float
    shade_required: bool = False
    shade_reason: str = ""
    effective_threshold: float = 0.0


@dataclass
class ShadeRequestFlow:
    """Request data for shading decision."""

    window_data: dict[str, Any]
    effective_config: dict[str, Any]
    external_states: dict[str, Any]
    scenario_b_enabled: bool
    scenario_c_enabled: bool
    solar_result: WindowCalculationResult


class FlowIntegrationMixin:
    """Mixin class for flow-based integration functionality."""

    # Type hint for hass attribute (provided by inheriting class)
    if TYPE_CHECKING:
        hass: HomeAssistant

    # The FlowIntegrationMixin expects the consuming class to provide a
    # number of helper methods (for example, provided by the coordinator
    # or other mixins). Stubs are provided here so static type checkers
    # can understand attribute access; runtime implementations must
    # override these methods.

    def _get_global_data_merged(self) -> dict[str, Any]:
        """
        Return merged global configuration data (stub for typing).

        Implementations should return a mapping of global config values.
        """
        raise NotImplementedError

    def _get_subentries_by_type(self, entry_type: str) -> dict[str, dict[str, Any]]:
        """
        Get all sub-entries of a specific type.

        Handles legacy, new type names, and subentries in parent configs.
        """
        subentries = {}

        # Map legacy and new type names for global config
        entry_type_map = {
            "global": ["global_config"],  # Standardized to global_config only
            "group": ["group"],
            "window": ["window"],
            "group_configs": ["group_configs"],
            "window_configs": ["window_configs"],
        }
        valid_types = entry_type_map.get(entry_type, [entry_type])

        # Get all config entries for this domain
        domain_entries = self.hass.config_entries.async_entries("solar_window_system")

        for entry in domain_entries:
            # Direct match (classic style)
            if entry.data.get("entry_type") in valid_types:
                subentries[entry.entry_id] = entry.data

            # For window/group: also check subentries in parent configs
            if entry_type in ("window", "group") and hasattr(entry, "subentries"):
                for sub in entry.subentries.values():
                    if hasattr(sub, "data") and hasattr(sub, "subentry_type"):
                        sub_data = (
                            dict(sub.data) if hasattr(sub.data, "items") else sub.data
                        )
                        sub_type = getattr(sub, "subentry_type", None) or sub_data.get(
                            "entry_type"
                        )
                        sub_id = getattr(sub, "subentry_id", None) or getattr(
                            sub, "title", None
                        )
                    elif isinstance(sub, dict):
                        sub_data = sub.get("data", {})
                        sub_type = sub_data.get("entry_type") or sub.get(
                            "subentry_type"
                        )
                        sub_id = sub.get("subentry_id") or sub.get("title")
                    else:
                        continue  # skip unknown subentry type
                    if (
                        sub_type == entry_type
                        or sub_data.get("entry_type") == entry_type
                    ) and sub_id:
                        subentries[sub_id] = sub_data

        return subentries

    def get_effective_config_from_flows(
        self, window_subentry_id: str
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Get effective configuration using flow-based inheritance."""
        # Basic implementation - return default configs
        default_config = {"threshold": 100.0, "enabled": True}
        window_config = {"area": 2.0, "azimuth": 180.0}

        _LOGGER.debug("Using default config for window: %s", window_subentry_id)
        return default_config, window_config

    def calculate_all_windows_from_flows(self) -> dict[str, Any]:
        """
        Calculate all window shading requirements using flow-based configuration.

        Returns:
            Dictionary with calculation results for all windows

        """
        # Clear cache at start of calculation run
        self._entity_cache.clear()  # type: ignore[attr-defined]
        self._cache_timestamp = time.time()  # type: ignore[attr-defined]

        global_data = self._get_global_data_merged()

        # Check if this coordinator should calculate windows
        if not self._should_calculate_windows():
            return self._get_empty_window_results()

        # Get windows and check if any exist
        windows = self._get_subentries_by_type("window")
        if not windows:
            _LOGGER.debug("No window subentries found; skipping calculations.")
            return {"windows": {}}

        # Get external states and perform calculations
        external_states = self._prepare_external_states(global_data)

        # Check minimum calculation conditions
        if not self._meets_calculation_conditions(external_states, global_data):
            return self._get_zero_window_results_for_windows(windows)

        # Perform main window calculations
        window_results = self._calculate_window_results(windows, external_states)

        # Calculate group aggregations and summary
        group_results = self._calculate_group_results(windows, window_results)
        summary = self._calculate_summary(window_results)

        # Return results in the structure expected by coordinator
        results = {
            "windows": window_results,
            "groups": group_results,
            "summary": summary,
        }

        _LOGGER.debug("calculation cycle finished")
        return results

    async def calculate_all_windows_from_flows_async(self) -> dict[str, Any]:
        """
        Calculate all window shading requirements using flow-based configuration.

        Async version with parallel batch processing.

        Returns:
            Dictionary with calculation results for all windows

        """
        # Clear cache at start of calculation run
        self._entity_cache.clear()  # type: ignore[attr-defined]
        self._cache_timestamp = time.time()  # type: ignore[attr-defined]

        global_data = self._get_global_data_merged()

        # Check if this coordinator should calculate windows
        if not self._should_calculate_windows():
            return self._get_empty_window_results()

        # Get windows and check if any exist
        windows = self._get_subentries_by_type("window")
        if not windows:
            _LOGGER.debug("No window subentries found; skipping calculations.")
            return {"windows": {}}

        # Get external states and perform calculations
        external_states = await self._prepare_external_states_async(global_data)

        # Check minimum calculation conditions
        if not self._meets_calculation_conditions(external_states, global_data):
            return self._get_zero_window_results_for_windows(windows)

        # Perform main window calculations with async batch processing
        window_results = await self._calculate_window_results_async(  # type: ignore[attr-defined]
            windows, external_states
        )

        # Calculate group aggregations and summary
        group_results = self._calculate_group_results(windows, window_results)
        summary = self._calculate_summary(window_results)

        # Return results in the structure expected by coordinator
        results = {
            "windows": window_results,
            "groups": group_results,
            "summary": summary,
        }

        _LOGGER.debug("async calculation cycle finished")
        return results

    def _should_shade_window_from_flows(
        self,
        shade_request: ShadeRequestFlow,
    ) -> tuple[bool, str]:
        """
        Flow-based shading decision with full scenario logic.

        Implements the same logic as should_shade_window() but for flow-based
        calculation.
        """
        window_name = shade_request.window_data.get("name", "Unknown")

        _LOGGER.debug("[SHADE-FLOW] ---- Shading Logic for %s ----", window_name)

        # Check maintenance mode
        if shade_request.external_states["maintenance_mode"]:
            _LOGGER.debug("[SHADE-FLOW] Result: OFF (Maintenance mode active)")
            return False, "Maintenance mode active"

        # Check weather warning override
        if shade_request.external_states["weather_warning"]:
            _LOGGER.debug("[SHADE-FLOW] Result: ON (Weather warning active)")
            return True, "Weather warning active"

        # Get indoor temperature from window, group, or global config
        try:

            def is_inherit_marker(val: Any) -> bool:
                return val in ("-1", -1, "", None, "inherit")

            # 1. Window-specific - prefer new key, but accept legacy key
            indoor_temp_entity = shade_request.window_data.get(
                "indoor_temperature_sensor", ""
            ) or shade_request.window_data.get("room_temp_entity", "")
            # 2. If not found or is inheritance marker, use effective config
            if not indoor_temp_entity or is_inherit_marker(indoor_temp_entity):
                indoor_temp_entity = shade_request.effective_config.get(
                    "indoor_temperature_sensor", ""
                ) or shade_request.effective_config.get("room_temp_entity", "")

            if not indoor_temp_entity:
                _LOGGER.warning(
                    "No room temperature sensor for window %s "
                    "(neither window, group, nor global config)",
                    window_name,
                )
                return False, "No room temperature sensor"

            indoor_temp_str = self._get_cached_entity_state(indoor_temp_entity, "0")  # type: ignore[attr-defined]
            indoor_temp = float(indoor_temp_str)
            outdoor_temp = shade_request.external_states["outdoor_temp"]

            _LOGGER.debug(
                "[SHADE-FLOW] Temps - Indoor: %.1f°C, Outdoor: %.1f°C",
                indoor_temp,
                outdoor_temp,
            )
        except (ValueError, TypeError):
            _LOGGER.warning("Could not parse temperature for window %s", window_name)
            return False, "Invalid temperature data"

        # Main shading decision logic
        return self._evaluate_shading_scenarios(
            shade_request, indoor_temp, outdoor_temp
        )

    def _evaluate_shading_scenarios(
        self,
        shade_request: ShadeRequestFlow,
        indoor_temp: float,
        outdoor_temp: float,
    ) -> tuple[bool, str]:
        """Evaluate all shading scenarios and return the result."""
        # --- Scenario A: Strong direct sun (always active) ---
        threshold_direct = shade_request.effective_config["thresholds"]["direct"]
        _LOGGER.debug(
            "[SHADE-FLOW] Scenario A Check: Power (%.1fW) > Threshold (%.1fW)? "
            "AND Indoor (%.1f°C) >= Base (%.1f°C)? "
            "AND Outdoor (%.1f°C) >= Base (%.1f°C)?",
            shade_request.solar_result.power_total,
            threshold_direct,
            indoor_temp,
            shade_request.effective_config["temperatures"]["indoor_base"],
            outdoor_temp,
            shade_request.effective_config["temperatures"]["outdoor_base"],
        )

        if (
            shade_request.solar_result.power_total > threshold_direct
            and indoor_temp
            >= shade_request.effective_config["temperatures"]["indoor_base"]
            and outdoor_temp
            >= shade_request.effective_config["temperatures"]["outdoor_base"]
        ):
            _LOGGER.debug("[SHADE-FLOW] Result: ON (Scenario A triggered)")
            power_val = shade_request.solar_result.power_total
            return (
                True,
                f"Strong sun ({power_val:.0f}W > {threshold_direct:.0f}W)",
            )

        # --- Scenario B: Diffuse heat ---
        scenario_b_config = shade_request.effective_config.get("scenario_b", {})
        if shade_request.scenario_b_enabled and scenario_b_config.get("enabled", True):
            result_b, reason_b = self._check_scenario_b(
                shade_request, scenario_b_config, indoor_temp, outdoor_temp
            )
            if result_b:
                return result_b, reason_b

        # --- Scenario C: Heatwave forecast ---
        # Check if scenario C is enabled (default to True if not specified)
        scenario_c_enabled_in_config = shade_request.effective_config.get(
            "scenario_c_enable", "inherit"
        )
        if shade_request.scenario_c_enabled and scenario_c_enabled_in_config not in (
            "disable",
            False,
        ):
            result_c, reason_c = self._check_scenario_c(shade_request, indoor_temp)
            if result_c:
                return result_c, reason_c

        _LOGGER.debug("[SHADE-FLOW] Result: OFF (No scenario triggered)")
        return False, "No shading required"

    def _check_scenario_b(
        self,
        shade_request: ShadeRequestFlow,
        scenario_b_config: dict[str, Any],
        indoor_temp: float,
        outdoor_temp: float,
    ) -> tuple[bool, str]:
        """Check scenario B: Diffuse heat."""
        threshold_diffuse = shade_request.effective_config["thresholds"]["diffuse"]
        temp_indoor_b = shade_request.effective_config["temperatures"][
            "indoor_base"
        ] + scenario_b_config.get("temp_indoor_offset", 0.5)
        temp_outdoor_b = shade_request.effective_config["temperatures"][
            "outdoor_base"
        ] + scenario_b_config.get("temp_outdoor_offset", 6.0)

        _LOGGER.debug(
            "[SHADE-FLOW] Scenario B Check: Power (%.1fW) > Threshold (%.1fW)? "
            "AND Indoor (%.1f°C) > Offset (%.1f°C)? "
            "AND Outdoor (%.1f°C) > Offset (%.1f°C)?",
            shade_request.solar_result.power_total,
            threshold_diffuse,
            indoor_temp,
            temp_indoor_b,
            outdoor_temp,
            temp_outdoor_b,
        )

        if (
            shade_request.solar_result.power_total > threshold_diffuse
            and indoor_temp > temp_indoor_b
            and outdoor_temp > temp_outdoor_b
        ):
            _LOGGER.debug("[SHADE-FLOW] Result: ON (Scenario B triggered)")
            power_val = shade_request.solar_result.power_total
            return (
                True,
                f"Diffuse heat ({power_val:.0f}W, Indoor: {indoor_temp:.1f}°C)",
            )
        return False, "No shading required"

    def _check_scenario_c(
        self,
        shade_request: ShadeRequestFlow,
        indoor_temp: float,
    ) -> tuple[bool, str]:
        """Check scenario C: Heatwave forecast."""
        try:
            forecast_temp = shade_request.external_states["forecast_temp"]
            if forecast_temp > 0:
                current_hour = datetime.now(UTC).hour
                # Read threshold from effective config instead of nested
                # scenario_c_config
                temp_forecast_threshold = shade_request.effective_config.get(
                    "scenario_c_temp_forecast", 28.5
                )
                start_hour = shade_request.effective_config.get(
                    "scenario_c_start_hour", 9
                )

                _LOGGER.debug(
                    "[SHADE-FLOW] Scenario C Check: Forecast (%.1f°C) > "
                    "Threshold (%.1f°C)? AND Indoor (%.1f°C) >= Base (%.1f°C)? "
                    "AND Hour (%d) >= Start (%d)?",
                    forecast_temp,
                    temp_forecast_threshold,
                    indoor_temp,
                    shade_request.effective_config["temperatures"]["indoor_base"],
                    current_hour,
                    start_hour,
                )

                if (
                    forecast_temp > temp_forecast_threshold
                    and indoor_temp
                    >= shade_request.effective_config["temperatures"]["indoor_base"]
                    and current_hour >= start_hour
                ):
                    _LOGGER.debug("[SHADE-FLOW] Result: ON (Scenario C triggered)")
                    return (
                        True,
                        f"Heatwave forecast ({forecast_temp:.1f}°C expected)",
                    )
        except (ValueError, TypeError):
            _LOGGER.warning("Could not read forecast temperature for Scenario C")

        return False, "No shading required"

    def _get_window_config_from_flow(self, window_id: str) -> dict[str, Any]:
        """
        Get window configuration from flow-based setup.

        Args:
            window_id: Window identifier

        Returns:
            Window configuration dictionary

        """
        try:
            # Get window subentries
            windows = self._get_subentries_by_type("window")
        except Exception:
            _LOGGER.exception("Error getting window config from flow for %s", window_id)
            return {}
        else:
            if window_id in windows:
                return windows[window_id]

            _LOGGER.warning("Window %s not found in flow configuration", window_id)
            return {}

    def _get_group_config_from_flow(self, group_id: str) -> dict[str, Any]:
        """
        Get group configuration from flow-based setup.

        Args:
            group_id: Group identifier

        Returns:
            Group configuration dictionary

        """
        try:
            # Get group subentries
            groups = self._get_subentries_by_type("group")
        except Exception:
            _LOGGER.exception("Error getting group config from flow for %s", group_id)
            return {}
        else:
            if group_id in groups:
                return groups[group_id]

            _LOGGER.warning("Group %s not found in flow configuration", group_id)
            return {}

    def _get_global_config_from_flow(self) -> dict[str, Any]:
        """
        Get global configuration from flow-based setup.

        Returns:
            Global configuration dictionary

        """
        try:
            # Get global subentries
            global_config = self._get_subentries_by_type("global")
        except Exception:
            _LOGGER.exception("Error getting global config from flow")
            return {}
        else:
            # For global config, we typically expect a single entry or merged config
            if global_config:
                # If there's a specific global entry, return it
                if "global" in global_config:
                    return global_config["global"]
                # Otherwise return the first available config
                return next(iter(global_config.values()))

            _LOGGER.warning("No global configuration found in flow setup")
            return {}

    def _get_scenario_enables_from_flows(
        self,
        window_subentry_id: str,
        global_states: dict[str, Any],
    ) -> tuple[bool, bool]:
        """
        Get scenario B and C enables with flow-based inheritance logic.

        Inheritance order: Window → Group → Global
        Values: "inherit" | "enable" | "disable"

        Returns:
            Tuple of (scenario_b_enabled, scenario_c_enabled)

        """
        # Get window data
        windows = self._get_subentries_by_type("window")
        window_data = windows.get(window_subentry_id, {})

        # Get parent group data if available
        parent_group_id = window_data.get("parent_group_id")
        group_data = {}
        if parent_group_id:
            groups = self._get_subentries_by_type("group")
            group_data = groups.get(parent_group_id, {})

        def resolve_scenario_enable(scenario_key: str, *, global_enabled: bool) -> bool:
            """Resolve inheritance for a single scenario."""
            # Check window level
            window_value = window_data.get(scenario_key, "inherit")
            if window_value in ["enable", "disable"]:
                return window_value == "enable"

            # Check group level
            if group_data:
                group_value = group_data.get(scenario_key, "inherit")
                if group_value in ["enable", "disable"]:
                    return group_value == "enable"

            # Fall back to global
            return global_enabled

        scenario_b_enabled = resolve_scenario_enable(
            "scenario_b_enable",
            global_enabled=global_states.get("scenario_b_enabled", False),
        )
        scenario_c_enabled = resolve_scenario_enable(
            "scenario_c_enable",
            global_enabled=global_states.get("scenario_c_enabled", False),
        )

        return scenario_b_enabled, scenario_c_enabled

    def _should_calculate_windows(self) -> bool:
        """Check if this coordinator should calculate windows."""
        entry_type = getattr(self.global_entry, "data", {}).get("entry_type", "")  # type: ignore[attr-defined]
        return entry_type == "window_configs"

    def _get_empty_window_results(self) -> dict[str, Any]:
        """Get empty window results when coordinator shouldn't calculate."""
        _LOGGER.debug(
            "Skipping calculations: entry_type '%s' does not calculate windows",
            getattr(self.global_entry, "data", {}).get("entry_type", ""),  # type: ignore[attr-defined]
        )
        windows = self._get_subentries_by_type("window")
        return {"windows": {k: {"shade_required": False} for k in windows}}

    def _prepare_external_states(self, global_data: dict[str, Any]) -> dict[str, Any]:
        """Prepare external states from global data."""
        _LOGGER.debug(
            "Using entity IDs: solar_radiation='%s', outdoor_temp='%s', "
            "forecast_temp='%s', weather_warning='%s'",
            global_data.get("solar_radiation_sensor", ""),
            global_data.get("outdoor_temperature_sensor", ""),
            global_data.get("weather_forecast_temperature_sensor", ""),
            global_data.get("weather_warning_sensor", ""),
        )

        return {
            "sensitivity": global_data.get("global_sensitivity", 1.0),
            "children_factor": global_data.get("children_factor", 0.8),
            "temperature_offset": global_data.get("temperature_offset", 0.0),
            "scenario_b_enabled": global_data.get("scenario_b_enabled", False),
            "scenario_c_enabled": global_data.get("scenario_c_enabled", False),
            "debug_mode": global_data.get("debug_mode", False),
            "maintenance_mode": global_data.get("maintenance_mode", False),
            "solar_radiation": float(
                self._get_cached_entity_state(  # type: ignore[attr-defined]
                    global_data.get("solar_radiation_sensor", ""), 0
                )
            ),
            "sun_azimuth": float(
                self.get_safe_attr(self.hass, "sun.sun", "azimuth", 0)  # type: ignore[attr-defined]
            ),
            "sun_elevation": float(
                self.get_safe_attr(self.hass, "sun.sun", "elevation", 0)  # type: ignore[attr-defined]
            ),
            "outdoor_temp": float(
                self._get_cached_entity_state(  # type: ignore[attr-defined]
                    global_data.get("outdoor_temperature_sensor", ""), 0
                )
            ),
            "forecast_temp": float(
                self._get_cached_entity_state(  # type: ignore[attr-defined]
                    global_data.get("weather_forecast_temperature_sensor", ""), 0
                )
            ),
            "weather_warning": self._get_cached_entity_state(  # type: ignore[attr-defined]
                global_data.get("weather_warning_sensor", ""), "off"
            )
            == "on",
        }

    async def _prepare_external_states_async(
        self, global_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Prepare external states from global data (async version)."""
        _LOGGER.debug(
            "Using entity IDs: solar_radiation='%s', outdoor_temp='%s', "
            "forecast_temp='%s', weather_warning='%s'",
            global_data.get("solar_radiation_sensor", ""),
            global_data.get("outdoor_temperature_sensor", ""),
            global_data.get("weather_forecast_temperature_sensor", ""),
            global_data.get("weather_warning_sensor", ""),
        )

        return {
            "sensitivity": global_data.get("global_sensitivity", 1.0),
            "children_factor": global_data.get("children_factor", 0.8),
            "temperature_offset": global_data.get("temperature_offset", 0.0),
            "scenario_b_enabled": global_data.get("scenario_b_enabled", False),
            "scenario_c_enabled": global_data.get("scenario_c_enabled", False),
            "debug_mode": global_data.get("debug_mode", False),
            "maintenance_mode": global_data.get("maintenance_mode", False),
            "solar_radiation": float(
                self._get_cached_entity_state(  # type: ignore[attr-defined]
                    global_data.get("solar_radiation_sensor", ""), 0
                )
            ),
            "sun_azimuth": float(
                self.get_safe_attr(self.hass, "sun.sun", "azimuth", 0)  # type: ignore[attr-defined]
            ),
            "sun_elevation": float(
                self.get_safe_attr(self.hass, "sun.sun", "elevation", 0)  # type: ignore[attr-defined]
            ),
            "outdoor_temp": float(
                self._get_cached_entity_state(  # type: ignore[attr-defined]
                    global_data.get("outdoor_temperature_sensor", ""), 0
                )
            ),
            "forecast_temp": float(
                self._get_cached_entity_state(  # type: ignore[attr-defined]
                    global_data.get("weather_forecast_temperature_sensor", ""), 0
                )
            ),
            "weather_warning": self._get_cached_entity_state(  # type: ignore[attr-defined]
                global_data.get("weather_warning_sensor", ""), "off"
            )
            == "on",
        }

    def _meets_calculation_conditions(
        self, external_states: dict[str, Any], global_config: dict[str, Any]
    ) -> bool:
        """Check if minimum calculation conditions are met."""
        min_radiation = external_states.get("solar_radiation", 0.0)
        min_elevation = external_states.get("sun_elevation", 0.0)

        # Get configured thresholds from global config, fallback to defaults
        min_radiation_threshold = global_config.get("min_solar_radiation", 1e-3)
        min_elevation_threshold = global_config.get("min_sun_elevation", 0.0)

        return (
            min_radiation >= min_radiation_threshold
            and min_elevation >= min_elevation_threshold
        )

    def _get_zero_window_results_for_windows(
        self, windows: dict[str, Any]
    ) -> dict[str, Any]:
        """Get zero window results for all windows when conditions not met."""
        window_results = {}
        for window_subentry_id, window_data in windows.items():
            window_results[window_subentry_id] = {
                "name": window_data.get("name", window_subentry_id),
                "total_power": 0,
                "total_power_direct": 0,
                "total_power_diffuse": 0,
                "total_power_raw": 0,
                "power_m2_total": 0,
                "power_m2_direct": 0,
                "power_m2_diffuse": 0,
                "power_m2_raw": 0,
                "shadow_factor": 0,
                "area_m2": 0,
                "is_visible": False,
                "shade_required": False,
                "shade_reason": "Minimum conditions not met",
                "effective_threshold": 0,
            }
        return {"windows": window_results}

    def _calculate_window_results(
        self, windows: dict[str, Any], external_states: dict[str, Any]
    ) -> dict[str, Any]:
        """Calculate results for all windows."""
        window_results = {}
        total_power = 0
        shading_count = 0

        for window_subentry_id, window_data in windows.items():
            try:
                result = self._calculate_single_window(  # type: ignore[attr-defined]
                    window_subentry_id, window_data, external_states
                )
                window_results[window_subentry_id] = result
                total_power += result["total_power"]
                if result["shade_required"]:
                    shading_count += 1

            except (ValueError, TypeError, KeyError, Exception) as err:
                _LOGGER.exception("Error calculating window %s", window_subentry_id)
                window_results[window_subentry_id] = self._get_error_window_result(  # type: ignore[attr-defined]
                    window_data, window_subentry_id, err
                )

        return window_results

    def _calculate_group_results(
        self, windows: dict[str, Any], window_results: dict[str, Any]
    ) -> dict[str, Any]:
        """Calculate group aggregation results."""
        group_results = {}
        groups = self._get_subentries_by_type("group")

        for group_id, group_data in groups.items():
            group_name = group_data.get("name", group_id)
            group_total_power = 0
            group_total_direct = 0
            group_total_diffuse = 0

            # Sum up all windows linked to this group
            for window_id, window_result in window_results.items():
                # Check if window is linked to this group (via window config)
                window_config = windows.get(window_id, {})
                if window_config.get("linked_group_id") == group_id:
                    group_total_power += window_result["total_power"]
                    group_total_direct += window_result["total_power_direct"]
                    group_total_diffuse += window_result["total_power_diffuse"]

            group_results[group_id] = {
                "name": group_name,
                "total_power": round(group_total_power, 2),
                "total_power_direct": round(group_total_direct, 2),
                "total_power_diffuse": round(group_total_diffuse, 2),
            }

        return group_results

    def _calculate_summary(self, window_results: dict[str, Any]) -> dict[str, Any]:
        """Calculate system-wide summary."""
        total_power_direct = sum(
            w["total_power_direct"] for w in window_results.values()
        )
        total_power_diffuse = sum(
            w["total_power_diffuse"] for w in window_results.values()
        )
        total_power = sum(w["total_power"] for w in window_results.values())
        windows_with_shading = sum(
            1 for w in window_results.values() if w["shade_required"]
        )
        shading_count = sum(1 for w in window_results.values() if w["shade_required"])

        return {
            "total_power": round(total_power, 2),
            "total_power_direct": round(total_power_direct, 2),
            "total_power_diffuse": round(total_power_diffuse, 2),
            "windows_with_shading": windows_with_shading,
            "window_count": len(window_results),
            "shading_count": shading_count,
            "calculation_time": datetime.now(UTC).isoformat(),
        }
