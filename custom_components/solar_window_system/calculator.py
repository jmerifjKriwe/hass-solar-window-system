"""Solar Window System calculator module."""

from __future__ import annotations

from datetime import UTC, datetime
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from .modules.cache import CacheMixin

# Import mixins for modular functionality
from .modules.calculations import CalculationsMixin
from .modules.config import ConfigMixin
from .modules.debug import DebugMixin
from .modules.flow_integration import (
    FlowIntegrationMixin,
    ShadeRequestFlow,
    WindowCalculationResult,
)
from .modules.flow_integration import (
    WindowCalculationResult as FlowWindowCalculationResult,
)
from .modules.shading import ShadingMixin
from .modules.utils import UtilsMixin

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class SolarCalculationError(HomeAssistantError):
    """Exception for solar calculation errors."""


class SolarWindowCalculator(
    CalculationsMixin,
    CacheMixin,
    ConfigMixin,
    DebugMixin,
    FlowIntegrationMixin,
    ShadingMixin,
    UtilsMixin,
):
    """
    Calculator for solar window shading requirements.

    This class handles all calculations related to determining when windows
    should be shaded based on solar radiation, elevation, and other factors.

    Now uses modular mixins for better maintainability and testing.
    """

    def __init__(
        self,
        hass: Any,
        defaults_config: dict[str, Any] | None = None,
        groups_config: dict[str, Any] | None = None,
        windows_config: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize the SolarWindowCalculator.

        Args:
            hass: Home Assistant instance
            defaults_config: Default configuration settings
            groups_config: Group-specific configuration settings
            windows_config: Window-specific configuration settings

        """
        # Initialize mixins first
        super().__init__()

        self.hass = hass
        self.defaults = defaults_config or {}
        self.groups = groups_config or {}
        self.windows = windows_config or {}

        # Flow-based attributes - will be set by __init_flow_based__
        self.global_entry = None

        _LOGGER.debug("Calculator initialized with %s windows.", len(self.windows))

    def apply_global_factors(
        self, config: dict[str, Any], group_type: str, states: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply global sensitivity and offset factors to configuration."""
        return super().apply_global_factors(config, group_type, states)

    # ==== NEW FLOW-BASED METHODS ====

    @classmethod
    def from_flows(
        cls, hass: HomeAssistant, entry: ConfigEntry
    ) -> SolarWindowCalculator:
        """Create calculator instance from flow-based configuration."""
        # Create instance with empty windows list first
        instance = cls(hass, {}, {})

        # Set up flow-based configuration
        instance.global_entry = entry

        _LOGGER.debug("Calculator initialized with flow-based configuration.")
        return instance

    def _calculate_direct_power(
        self,
        params: dict[str, float],
        window_azimuth: float,
    ) -> float:
        """
        Calculate direct solar power component.

        Uses the modular CalculationsMixin implementation.
        """
        return super()._calculate_direct_power(params, window_azimuth)

    def calculate_window_solar_power_with_shadow(
        self,
        effective_config: dict[str, Any],
        window_data: dict[str, Any],
        states: dict[str, Any],
    ) -> WindowCalculationResult:
        """
        Calculate solar power for a window including shadow effects.

        Args:
            effective_config: Effective configuration after inheritance
            window_data: Window-specific data from subentry
            states: External state data (sun position, etc.)

        Returns:
            WindowCalculationResult with calculated values

        """
        # Extract parameters
        (
            solar_radiation,
            sun_azimuth,
            sun_elevation,
            g_value,
            diffuse_factor,
            tilt,
            area,
            shadow_depth,
            shadow_offset,
        ) = self._extract_calculation_parameters(effective_config, window_data, states)

        # Thresholds for minimum radiation and elevation
        min_radiation = 1e-3
        min_elevation = 0.0

        # Check if minimums are met; if not, skip calculation
        if solar_radiation < min_radiation or sun_elevation < min_elevation:
            return WindowCalculationResult(
                power_total=0.0,
                power_direct=0.0,
                power_diffuse=0.0,
                power_direct_raw=0.0,
                power_diffuse_raw=0.0,
                power_total_raw=0.0,
                shadow_factor=1.0,
                is_visible=False,
                area_m2=0.0,
                shade_required=False,
                shade_reason="",
                effective_threshold=effective_config.get("thresholds", {}).get(
                    "direct", 200.0
                ),
            )

        # Calculate diffuse power (not affected by shadows)
        power_diffuse = solar_radiation * diffuse_factor * area * g_value
        power_direct = 0
        power_direct_raw = 0
        power_diffuse_raw = power_diffuse  # Diffuse is never affected by shadows
        is_visible = False
        shadow_factor = 1.0

        # Check window visibility
        is_visible, window_azimuth = super()._check_window_visibility(
            sun_elevation, sun_azimuth, window_data, effective_config
        )

        _LOGGER.debug(
            "Solar Power Calculation for %s: sun_el=%.1f°, sun_az=%.1f°, "
            "window_az=%.1f°, shadow_depth=%.2fm, shadow_offset=%.2fm",
            window_data.get("name", "Unknown"),
            sun_elevation,
            sun_azimuth,
            window_azimuth,
            shadow_depth,
            shadow_offset,
        )

        if is_visible:
            _LOGGER.debug("Sun is VISIBLE to the window.")

            # Calculate direct power
            params = {
                "solar_radiation": solar_radiation,
                "sun_elevation": sun_elevation,
                "sun_azimuth": sun_azimuth,
                "diffuse_factor": diffuse_factor,
                "tilt": tilt,
                "area": area,
                "g_value": g_value,
            }
            power_direct_raw = self._calculate_direct_power(params, window_azimuth)

            # Store raw values before shadow calculation
            power_direct = power_direct_raw

            # Apply shadow calculation
            if shadow_depth > 0 or shadow_offset > 0:
                shadow_factor = self._calculate_shadow_factor(
                    sun_elevation,
                    sun_azimuth,
                    window_azimuth,
                    shadow_depth,
                    shadow_offset,
                    window_data,
                )
                power_direct *= shadow_factor
                _LOGGER.debug("Shadow factor applied: %.2f", shadow_factor)

        _LOGGER.debug(
            "Power calculation result: direct=%.2fW, diffuse=%.2fW, "
            "total=%.2fW, shadow_factor=%.2f",
            power_direct,
            power_diffuse,
            power_direct + power_diffuse,
            shadow_factor,
        )

        return WindowCalculationResult(
            power_total=power_direct + power_diffuse,
            power_direct=power_direct,
            power_diffuse=power_diffuse,
            power_direct_raw=power_direct_raw,
            power_diffuse_raw=power_diffuse_raw,
            power_total_raw=power_direct_raw + power_diffuse_raw,
            shadow_factor=shadow_factor,
            is_visible=is_visible,
            area_m2=area,
            shade_required=False,  # Will be set by shading logic
            shade_reason="",  # Will be set by shading logic
            effective_threshold=effective_config.get("thresholds", {}).get(
                "direct", 200.0
            ),
        )

    def calculate_all_windows_from_flows(self) -> dict[str, Any]:
        """Calculate all window shading requirements using flow-based configuration."""
        return super().calculate_all_windows_from_flows()

    async def calculate_all_windows_from_flows_async(self) -> dict[str, Any]:
        """Calculate all window shading requirements using flow-based configuration."""
        return await super().calculate_all_windows_from_flows_async()

    def _should_calculate_windows(self) -> bool:
        """Check if this coordinator should calculate windows."""
        entry_type = getattr(self.global_entry, "data", {}).get("entry_type", "")
        return entry_type == "window_configs"

    def _get_empty_window_results(self) -> dict[str, Any]:
        """Get empty window results when coordinator shouldn't calculate."""
        _LOGGER.debug(
            "Skipping calculations: entry_type '%s' does not calculate windows",
            getattr(self.global_entry, "data", {}).get("entry_type", ""),
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
                super()._get_cached_entity_state(
                    global_data.get("solar_radiation_sensor", ""), 0
                )
            ),
            "sun_azimuth": float(
                super().get_safe_attr(self.hass, "sun.sun", "azimuth", 0)
            ),
            "sun_elevation": float(
                super().get_safe_attr(self.hass, "sun.sun", "elevation", 0)
            ),
            "outdoor_temp": float(
                super()._get_cached_entity_state(
                    global_data.get("outdoor_temperature_sensor", ""), 0
                )
            ),
            "forecast_temp": float(
                super()._get_cached_entity_state(
                    global_data.get("weather_forecast_temperature_sensor", ""), 0
                )
            ),
            "weather_warning": super()._get_cached_entity_state(
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
                super()._get_cached_entity_state(
                    global_data.get("solar_radiation_sensor", ""), 0
                )
            ),
            "sun_azimuth": float(
                super().get_safe_attr(self.hass, "sun.sun", "azimuth", 0)
            ),
            "sun_elevation": float(
                super().get_safe_attr(self.hass, "sun.sun", "elevation", 0)
            ),
            "outdoor_temp": float(
                super()._get_cached_entity_state(
                    global_data.get("outdoor_temperature_sensor", ""), 0
                )
            ),
            "forecast_temp": float(
                super()._get_cached_entity_state(
                    global_data.get("weather_forecast_temperature_sensor", ""), 0
                )
            ),
            "weather_warning": super()._get_cached_entity_state(
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
                result = self._calculate_single_window(
                    window_subentry_id, window_data, external_states
                )
                window_results[window_subentry_id] = result
                total_power += result["total_power"]
                if result["shade_required"]:
                    shading_count += 1

            except (ValueError, TypeError, KeyError, Exception) as err:
                _LOGGER.exception("Error calculating window %s", window_subentry_id)
                window_results[window_subentry_id] = self._get_error_window_result(
                    window_data, window_subentry_id, err
                )

        return window_results

    async def _calculate_window_results_async(
        self, windows: dict[str, Any], external_states: dict[str, Any]
    ) -> dict[str, Any]:
        """Calculate results for all windows (async version)."""
        window_results = {}
        total_power = 0
        shading_count = 0

        # Prepare window data for batch processing
        window_data_list = []
        window_ids = []

        for window_subentry_id, window_data in windows.items():
            window_ids.append(window_subentry_id)
            window_data_list.append((window_subentry_id, window_data))

        # Process windows in parallel using batch calculation
        batch_results = await self._batch_calculate_windows_async(
            window_data_list, external_states
        )

        # Process results
        for i, result in enumerate(batch_results):
            window_subentry_id = window_ids[i]
            try:
                window_results[window_subentry_id] = result
                total_power += result["total_power"]
                if result["shade_required"]:
                    shading_count += 1
            except (ValueError, TypeError, KeyError, Exception) as err:
                _LOGGER.exception("Error processing window %s", window_subentry_id)
                window_results[window_subentry_id] = self._get_error_window_result(
                    windows[window_subentry_id], window_subentry_id, err
                )

        return window_results

    async def _batch_calculate_windows_async(
        self,
        window_data_list: list[tuple[str, dict[str, Any]]],
        external_states: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Batch calculate multiple windows asynchronously."""
        # Prepare data for batch processing
        windows_data = []
        effective_configs = []

        for window_subentry_id, window_data in window_data_list:
            # Get effective configuration
            effective_config, _ = self.get_effective_config_from_flows(
                window_subentry_id
            )

            # Apply global factors
            group_type = window_data.get("group_type", "default")
            effective_config = self.apply_global_factors(
                effective_config, group_type, external_states
            )

            windows_data.append(window_data)
            effective_configs.append(effective_config)

        # Use the async batch calculation from CalculationsMixin
        solar_results = await self.batch_calculate_windows(
            windows_data, effective_configs, external_states
        )

        # Convert WindowCalculationResult objects to dictionaries
        results = []
        for i, solar_result in enumerate(solar_results):
            window_subentry_id = window_data_list[i][0]
            window_data = window_data_list[i][1]

            result = self._convert_solar_result_to_dict(
                solar_result, window_subentry_id, window_data, external_states
            )
            results.append(result)

        return results

    def _convert_solar_result_to_dict(
        self,
        solar_result: FlowWindowCalculationResult,
        window_subentry_id: str,
        window_data: dict[str, Any],
        external_states: dict[str, Any],
    ) -> dict[str, Any]:
        """Convert WindowCalculationResult to dictionary format."""
        # Get scenario enables for this window with inheritance logic
        (
            scenario_b_enabled,
            scenario_c_enabled,
        ) = self._get_scenario_enables_from_flows(window_subentry_id, external_states)

        # Get effective configuration for shading logic
        effective_config, _ = self.get_effective_config_from_flows(window_subentry_id)

        # Check shading requirement with full scenario logic
        shade_request = ShadeRequestFlow(
            window_data=window_data,
            effective_config=effective_config,
            external_states=external_states,
            scenario_b_enabled=scenario_b_enabled,
            scenario_c_enabled=scenario_c_enabled,
            solar_result=solar_result,
        )
        shade_required, shade_reason = self._should_shade_window_from_flows(
            shade_request
        )

        # Update result
        solar_result.shade_required = shade_required
        solar_result.shade_reason = shade_reason

        # Calculate additional metrics using the correct raw power values
        power_raw = solar_result.power_total_raw
        # Avoid division by zero
        area = solar_result.area_m2 if solar_result.area_m2 > 0 else 1

        # Return results in the correct structure for coordinator
        return {
            "name": window_data.get("name", window_subentry_id),
            "total_power": round(solar_result.power_total, 2),
            "total_power_direct": round(solar_result.power_direct, 2),
            "total_power_diffuse": round(solar_result.power_diffuse, 2),
            "total_power_raw": round(power_raw, 2),
            "power_m2_total": round(solar_result.power_total / area, 2),
            "power_m2_direct": round(solar_result.power_direct / area, 2),
            "power_m2_diffuse": round(solar_result.power_diffuse / area, 2),
            "power_m2_raw": round(power_raw / area, 2),
            "shadow_factor": solar_result.shadow_factor,
            "area_m2": solar_result.area_m2,
            "is_visible": solar_result.is_visible,
            "shade_required": solar_result.shade_required,
            "shade_reason": solar_result.shade_reason,
            "effective_threshold": solar_result.effective_threshold,
        }

    def _calculate_single_window(
        self,
        window_subentry_id: str,
        window_data: dict[str, Any],
        external_states: dict[str, Any],
    ) -> dict[str, Any]:
        """Calculate result for a single window."""
        try:
            # Get effective configuration and sources
            effective_config, effective_sources = self.get_effective_config_from_flows(
                window_subentry_id
            )

            # Apply global factors
            group_type = window_data.get("group_type", "default")
            effective_config = self.apply_global_factors(
                effective_config, group_type, external_states
            )

            # Calculate solar power with shadows
            solar_result = self.calculate_window_solar_power_with_shadow(
                effective_config, window_data, external_states
            )

            # Get scenario enables for this window with inheritance logic
            (
                scenario_b_enabled,
                scenario_c_enabled,
            ) = self._get_scenario_enables_from_flows(
                window_subentry_id, external_states
            )

            # Check shading requirement with full scenario logic
            shade_request = ShadeRequestFlow(
                window_data=window_data,
                effective_config=effective_config,
                external_states=external_states,
                scenario_b_enabled=scenario_b_enabled,
                scenario_c_enabled=scenario_c_enabled,
                solar_result=solar_result,
            )
            shade_required, shade_reason = self._should_shade_window_from_flows(
                shade_request
            )

            # Update result
            solar_result.shade_required = shade_required
            solar_result.shade_reason = shade_reason

            # Calculate additional metrics using the correct raw power values
            power_raw = solar_result.power_total_raw
            # Avoid division by zero
            area = solar_result.area_m2 if solar_result.area_m2 > 0 else 1

            # Return results in the correct structure for coordinator
            return {
                "name": window_data.get("name", window_subentry_id),
                "total_power": round(solar_result.power_total, 2),
                "total_power_direct": round(solar_result.power_direct, 2),
                "total_power_diffuse": round(solar_result.power_diffuse, 2),
                "total_power_raw": round(power_raw, 2),
                "power_m2_total": round(solar_result.power_total / area, 2),
                "power_m2_direct": round(solar_result.power_direct / area, 2),
                "power_m2_diffuse": round(solar_result.power_diffuse / area, 2),
                "power_m2_raw": round(power_raw / area, 2),
                "shadow_factor": solar_result.shadow_factor,
                "area_m2": solar_result.area_m2,
                "is_visible": solar_result.is_visible,
                "shade_required": solar_result.shade_required,
                "shade_reason": solar_result.shade_reason,
                "effective_threshold": solar_result.effective_threshold,
            }
        except Exception as err:
            _LOGGER.exception("Error calculating window %s", window_subentry_id)
            return self._get_error_window_result(window_data, window_subentry_id, err)

    def _get_error_window_result(
        self, window_data: dict[str, Any], window_subentry_id: str, err: Exception
    ) -> dict[str, Any]:
        """Get error result for a window calculation."""
        return {
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
            "shade_reason": f"Calculation error: {err}",
            "effective_threshold": 0,
        }

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

    def _get_scenario_enables_from_flows(
        self,
        window_subentry_id: str,
        global_states: dict[str, Any],
    ) -> tuple[bool, bool]:
        """
        Get scenario B and C enables with flow-based inheritance logic.

        Delegates to FlowIntegrationMixin implementation.
        """
        return super()._get_scenario_enables_from_flows(
            window_subentry_id, global_states
        )

    def _should_shade_window_from_flows(
        self,
        shade_request: ShadeRequestFlow,
    ) -> tuple[bool, str]:
        """
        Flow-based shading decision with full scenario logic.

        Delegates to FlowIntegrationMixin implementation.
        """
        return super()._should_shade_window_from_flows(shade_request)

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

    def create_debug_data(self, window_id: str) -> dict[str, Any] | None:
        """Create comprehensive debug data for a specific window."""
        return super().create_debug_data(window_id)

    def _collect_sensor_data(self) -> dict[str, Any]:
        """Collect current states of all relevant sensors."""
        global_data = self._get_global_data_merged()

        sensor_data = {}
        sensor_entities = [
            ("solar_radiation", global_data.get("solar_radiation_sensor")),
            ("outdoor_temperature", global_data.get("outdoor_temperature_sensor")),
            ("indoor_temperature", global_data.get("indoor_temperature_sensor")),
            (
                "weather_forecast_temperature",
                global_data.get("weather_forecast_temperature_sensor"),
            ),
            ("weather_warning", global_data.get("weather_warning_sensor")),
        ]

        for name, entity_id in sensor_entities:
            if entity_id:
                sensor_data[name] = {
                    "entity_id": entity_id,
                    "state": super().get_safe_state(self.hass, entity_id),
                    "available": self.hass.states.get(entity_id) is not None,
                }
            else:
                sensor_data[name] = {
                    "entity_id": None,
                    "state": None,
                    "available": False,
                }

        # Add sun.sun position data for debugging visibility calculations
        sun_entity_id = "sun.sun"
        sun_state = self.hass.states.get(sun_entity_id)
        if sun_state and sun_state.attributes:
            sensor_data["sun_position"] = {
                "entity_id": sun_entity_id,
                "elevation": sun_state.attributes.get("elevation", 0),
                "azimuth": sun_state.attributes.get("azimuth", 0),
                "available": True,
            }
        else:
            sensor_data["sun_position"] = {
                "entity_id": sun_entity_id,
                "elevation": 0,
                "azimuth": 0,
                "available": False,
            }

        return sensor_data

    def _collect_current_sensor_states(self, window_id: str) -> dict[str, Any]:
        """
        Collect current states of all Solar Window System sensors.

        Args:
            window_id: The ID of the window to collect sensor states for

        Returns:
            Dictionary with current sensor states organized by level

        """
        # Get base sensor states from DebugMixin
        sensor_states = super()._collect_current_sensor_states(window_id)

        # Initialize debug_info section if not present
        if "debug_info" not in sensor_states:
            sensor_states["debug_info"] = {
                "entities_found": 0,
                "search_attempts": [],
                "total_entities_in_registry": 0,
            }

        # Update total entities count
        try:
            entity_reg = er.async_get(self.hass)
            sensor_states["debug_info"]["total_entities_in_registry"] = len(
                [
                    entity_id
                    for entity_id in entity_reg.entities
                    if entity_id.startswith("sensor.sws_")
                ]
            )
        except Exception:
            _LOGGER.exception("Error getting entity registry count")

        # Initialize level-specific sections
        sensor_states["window_level"] = {}
        sensor_states["group_level"] = {}
        sensor_states["global_level"] = {}

        # Get window and group names for searching
        try:
            windows = self._get_subentries_by_type("window")
            if window_id in windows:
                window_config = windows[window_id]
                window_name = window_config.get("name", window_id)

                # Search for window-level sensors
                self._search_window_sensors(sensor_states, window_name)

                # Search for group-level sensors if window has a group
                group_id = window_config.get("linked_group_id")
                if group_id:
                    groups = self._get_subentries_by_type("group")
                    if group_id in groups:
                        self._search_group_sensors(sensor_states, window_id, groups)

            # Search for global-level sensors
            self._search_global_sensors(sensor_states)

        except Exception:
            _LOGGER.exception("Error during sensor search")

        return sensor_states

    def _validate_temperature_range(
        self, temp: float, min_temp: float = -50.0, max_temp: float = 60.0
    ) -> bool:
        """
        Validate temperature is within reasonable range.

        Uses the modular UtilsMixin implementation.
        """
        return super()._validate_temperature_range(temp, min_temp, max_temp)

    def _search_window_sensors(self, hass: Any, window_name: str) -> list[str]:
        """Search for window-level sensors."""
        # Delegate to DebugMixin implementation
        return super()._search_window_sensors(hass, window_name)

    def _search_group_sensors(
        self, hass: Any, window_id: str, groups: dict[str, Any]
    ) -> list[str]:
        """Search for group-level sensors."""
        # Delegate to DebugMixin implementation
        return super()._search_group_sensors(hass, window_id, groups)

    def _search_global_sensors(self, hass: Any) -> list[str]:
        """Search for global-level sensors."""
        # Delegate to DebugMixin implementation
        return super()._search_global_sensors(hass)

    def _find_entity_by_name(
        self,
        entity_name: str,
        entity_type: str = "global",
        window_name: str | None = None,
        group_name: str | None = None,
    ) -> str | None:
        """
        Find entity ID by entity name with Solar Window System specific search.

        Args:
            entity_name: The name of the entity to find
            entity_type: Type of entity ("window", "group", "global")
            window_name: Window name for window-specific entities
            group_name: Group name for group-specific entities

        Returns:
            Entity ID if found, None otherwise

        Uses the modular DebugMixin implementation.

        """
        return super()._find_entity_by_name(
            self.hass, entity_name, entity_type, window_name, group_name
        )
