"""
Solar power calculations and physical computations.

This module contains all solar power calculation logic,
and physical parameter handling.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
import math
from typing import Any

from .flow_integration import ShadeRequestFlow, WindowCalculationResult
from .shadow import calculate_shadow_factor, get_window_geometry

_LOGGER = logging.getLogger(__name__)

# Trigonometric Lookup Table for common angles (0-90 degrees)
# Pre-computed values to avoid repeated math calculations
TRIG_LUT = {
    angle: {
        "radians": math.radians(angle),
        "cos": math.cos(math.radians(angle)),
        "sin": math.sin(math.radians(angle)),
    }
    for angle in range(91)  # 0 to 90 degrees
}


def get_trig_values(angle_deg: float) -> dict[str, float]:
    """
    Get pre-computed trigonometric values for an angle in degrees.

    Args:
        angle_deg: Angle in degrees

    Returns:
        Dict with 'radians', 'cos', 'sin' values

    """
    # Round to nearest degree for lookup
    angle_key = round(angle_deg)
    if angle_key in TRIG_LUT:
        return TRIG_LUT[angle_key]
    # Fallback for angles outside 0-90 or non-integer
    rad = math.radians(angle_deg)
    return {"radians": rad, "cos": math.cos(rad), "sin": math.sin(rad)}


class WindowCalculationResultPool:
    """Memory pool for WindowCalculationResult objects to reduce GC pressure."""

    def __init__(self, max_size: int = 100) -> None:
        """Initialize the result pool."""
        self._pool: list[WindowCalculationResult] = []
        self._max_size = max_size
        self._borrowed = 0

    def acquire(self) -> WindowCalculationResult:
        """Acquire a WindowCalculationResult from the pool or create new one."""
        self._borrowed += 1

        if self._pool:
            # Reuse existing object - reset all values to defaults
            result = self._pool.pop()
            result.power_total = 0.0
            result.power_direct = 0.0
            result.power_diffuse = 0.0
            result.power_direct_raw = 0.0
            result.power_diffuse_raw = 0.0
            result.power_total_raw = 0.0
            result.shadow_factor = 1.0
            result.is_visible = False
            result.area_m2 = 0.0
            result.shade_required = False
            result.shade_reason = ""
            result.effective_threshold = 0.0
            return result

        # Create new object with default values
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
            effective_threshold=0.0,
        )

    def release(self, result: WindowCalculationResult) -> None:
        """Return a WindowCalculationResult to the pool."""
        if self._borrowed > 0:
            self._borrowed -= 1

        if len(self._pool) < self._max_size:
            self._pool.append(result)

    def get_stats(self) -> dict[str, int]:
        """Get pool statistics."""
        return {
            "pool_size": len(self._pool),
            "borrowed": self._borrowed,
            "max_size": self._max_size,
        }


# Global result pool instance
_RESULT_POOL = WindowCalculationResultPool()


def get_pooled_result() -> WindowCalculationResult:
    """Get a WindowCalculationResult from the pool."""
    return _RESULT_POOL.acquire()


def release_pooled_result(result: WindowCalculationResult) -> None:
    """Return a WindowCalculationResult to the pool."""
    _RESULT_POOL.release(result)


def get_pool_stats() -> dict[str, int]:
    """Get memory pool statistics."""
    return _RESULT_POOL.get_stats()


# Shadow geometry is provided by the dedicated shadow module. Keep this
# module focused on calculation helpers and reuse the ShadowGeometry type
# from `modules.shadow` to avoid duplicated definitions and mismatched
# defaults.


@dataclass
class SolarCalculationParams:
    """Parameters for solar power calculations."""

    # All fields are required and must be provided by callers. This
    # dataclass intentionally has no defaults to avoid accidental
    # reliance on hard-coded fallback values. Callers must construct a
    # fully-populated instance from values supplied by
    # effective_config/window_data/states.
    solar_radiation: float
    sun_elevation: float
    sun_azimuth: float
    window_azimuth: float
    area: float
    g_value: float
    tilt: float
    diffuse_factor: float


class CalculationsMixin:
    """Mixin class for calculation functionality."""

    async def batch_calculate_windows(
        self,
        windows_data: list[dict[str, Any]],
        effective_configs: list[dict[str, Any]],
        states: dict[str, Any],
    ) -> list[WindowCalculationResult]:
        """
        Calculate solar power for multiple windows in batch using parallel processing.

        Args:
            windows_data: List of window-specific data and parameters
            effective_configs: List of effective configurations for windows
            states: Current entity states

        Returns:
            List of WindowCalculationResult objects

        """
        # Create tasks for parallel execution
        tasks = []
        for window_data, effective_config in zip(
            windows_data, effective_configs, strict=True
        ):
            task = self._calculate_window_task(effective_config, window_data, states)
            tasks.append(task)

        # Execute all calculations in parallel
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        except Exception:
            _LOGGER.exception("Error in parallel batch calculation")
            # Fallback to sequential processing on error
            return self._batch_calculate_windows_sequential(
                windows_data, effective_configs, states
            )

        # Handle exceptions and convert to results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                _LOGGER.exception("Error in parallel calculation for window %d", i)
                window_area = windows_data[i].get("area", 2.0)
                final_results.append(
                    WindowCalculationResult(
                        power_total=0.0,
                        power_direct=0.0,
                        power_diffuse=0.0,
                        power_direct_raw=0.0,
                        power_diffuse_raw=0.0,
                        power_total_raw=0.0,
                        shadow_factor=1.0,
                        is_visible=False,
                        area_m2=window_area,
                        shade_required=False,
                        shade_reason=f"Parallel calculation error: {result!r}",
                        effective_threshold=0.0,
                    )
                )
            else:
                final_results.append(result)

        return final_results

    async def _calculate_window_task(
        self,
        effective_config: dict[str, Any],
        window_data: dict[str, Any],
        states: dict[str, Any],
    ) -> WindowCalculationResult:
        """Task wrapper for individual window calculation."""
        return await self.calculate_window_solar_power_with_shadow_async(
            effective_config, window_data, states
        )

    def _batch_calculate_windows_sequential(
        self,
        windows_data: list[dict[str, Any]],
        effective_configs: list[dict[str, Any]],
        states: dict[str, Any],
    ) -> list[WindowCalculationResult]:
        """Fallback sequential batch calculation."""
        results = []
        for window_data, effective_config in zip(
            windows_data, effective_configs, strict=True
        ):
            try:
                result = self.calculate_window_solar_power_with_shadow(
                    effective_config, window_data, states
                )
                results.append(result)
            except Exception as err:
                _LOGGER.exception("Error in sequential batch calculation for window")
                window_area = window_data.get("area", 2.0)
                results.append(
                    WindowCalculationResult(
                        power_total=0.0,
                        power_direct=0.0,
                        power_diffuse=0.0,
                        power_direct_raw=0.0,
                        power_diffuse_raw=0.0,
                        power_total_raw=0.0,
                        shadow_factor=1.0,
                        is_visible=False,
                        area_m2=window_area,
                        shade_required=False,
                        shade_reason=f"Sequential calculation error: {err!r}",
                        effective_threshold=0.0,
                    )
                )
        return results

    async def calculate_window_solar_power_with_shadow_async(
        self,
        effective_config: dict[str, Any],
        window_data: dict[str, Any],
        states: dict[str, Any],
    ) -> WindowCalculationResult:
        """
        Async wrapper for solar power calculation including shadow effects.

        Args:
            effective_config: Effective configuration for the window
            window_data: Window-specific data and parameters
            states: Current entity states

        Returns:
            WindowCalculationResult with calculated values

        Note:
            This is an async wrapper around the main implementation that exists
            for compatibility with async batch processing. It delegates all work
            to the main calculate_window_solar_power_with_shadow method.

        """
        # Delegate to the main implementation
        return self.calculate_window_solar_power_with_shadow(
            effective_config, window_data, states
        )

    def calculate_window_solar_power_with_shadow(
        self,
        effective_config: dict[str, Any],  # Contains all configuration values
        window_data: dict[str, Any],
        states: dict[str, Any],  # kept for API compatibility
    ) -> WindowCalculationResult:
        """
        Calculate solar power for a window including shadow effects.

        Args:
            effective_config: Effective configuration for the window
            window_data: Window-specific data and parameters
            states: Current entity states

        Returns:
            WindowCalculationResult with calculated values

        """
        try:
            # Extract required values from states. Missing values are
            # treated as errors to enforce the "no defaults in
            # production" rule; tests must provide these values via
            # the states fixture or effective configuration where
            # appropriate.
            try:
                sun_elevation = float(states["sun_elevation"])
                sun_azimuth = float(states["sun_azimuth"])
                solar_irradiance = float(states["solar_radiation"])
            except KeyError as exc:
                raise ValueError(
                    "Missing required state value: sun_elevation, sun_azimuth or solar_radiation"
                ) from exc
            except (TypeError, ValueError) as exc:
                raise ValueError("Invalid state value for solar inputs") from exc

            # Prefer explicit 'area' if provided by window_data. Otherwise
            # compute glass area from dimensions, subtracting frame width
            # when available in effective_config (keeps behavior consistent
            # with _extract_calculation_parameters).
            # Compute area: require either explicit 'area' or both
            # 'window_width' and 'window_height' in window_data. Do not
            # fall back to safe defaults here.
            if "area" in window_data:
                try:
                    window_area = float(window_data["area"])
                except (TypeError, ValueError) as exc:
                    raise ValueError("Invalid numeric value for window.area") from exc
            else:
                # Require explicit dimensions
                try:
                    window_width = float(window_data["window_width"])
                    window_height = float(window_data["window_height"])
                except KeyError as exc:
                    raise ValueError(
                        "Missing required window dimension: window_width or window_height"
                    ) from exc
                except (TypeError, ValueError) as exc:
                    raise ValueError("Invalid numeric window dimension") from exc

                # Frame width must be provided in effective_config.physical
                phys = effective_config.get("physical")
                if not isinstance(phys, dict) or "frame_width" not in phys:
                    raise ValueError(
                        "Missing required physical.frame_width in effective_config"
                    )
                try:
                    frame_width = float(phys["frame_width"])
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        "Invalid numeric value for physical.frame_width"
                    ) from exc

                glass_width = max(0.0, window_width - 2 * frame_width)
                glass_height = max(0.0, window_height - 2 * frame_width)
                window_area = glass_width * glass_height

            # Calculate shadow factor using shadow module
            geometry = get_window_geometry(
                sun_elevation, sun_azimuth, window_data, effective_config
            )
            shadow_factor = calculate_shadow_factor(geometry)

            # Get physical parameters from effective configuration and
            # require presence.
            physical_config = effective_config.get("physical")
            if not isinstance(physical_config, dict):
                raise ValueError(
                    "Missing required 'physical' section in effective_config"
                )
            try:
                g_value = float(physical_config["g_value"])
                diffuse_factor = float(physical_config["diffuse_factor"])
            except KeyError as exc:
                raise ValueError(
                    "Missing required physical.g_value or physical.diffuse_factor"
                ) from exc
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "Invalid numeric value in physical configuration"
                ) from exc

            # Calculate direct power with configured g-value
            direct_power = (
                solar_irradiance
                * max(0, get_trig_values(sun_elevation)["cos"])
                * g_value
            )

            # Calculate diffuse power with configured factor
            diffuse_power = solar_irradiance * diffuse_factor * g_value

            # Calculate total power per square meter
            total_power_per_m2 = (direct_power + diffuse_power) * shadow_factor

            # Calculate window area power
            total_window_power = total_power_per_m2 * window_area

            # Get threshold from effective configuration and require it
            thresholds = effective_config.get("thresholds")
            if not isinstance(thresholds, dict) or "direct" not in thresholds:
                raise ValueError(
                    "Missing required thresholds.direct in effective_config"
                )
            try:
                shade_threshold = float(thresholds["direct"])
            except (TypeError, ValueError) as exc:
                raise ValueError("Invalid numeric value for thresholds.direct") from exc

            should_shade = total_window_power > shade_threshold

            # Create result
            result = WindowCalculationResult(
                power_total=total_window_power,
                power_direct=direct_power * window_area,
                power_diffuse=diffuse_power * window_area,
                power_direct_raw=direct_power,
                power_diffuse_raw=diffuse_power,
                power_total_raw=total_power_per_m2,
                shadow_factor=shadow_factor,
                is_visible=True,  # Assume visible for now
                area_m2=window_area,
                shade_required=should_shade,
                shade_reason="High solar power detected" if should_shade else "",
                effective_threshold=shade_threshold,
            )

            _LOGGER.debug(
                "Calculated solar power for window: %.2f W",
                total_window_power,
            )

        except ValueError as err:
            # Known validation errors: log and return an error result so
            # callers can see the reason and tests can assert on it.
            _LOGGER.error("Validation error calculating solar power: %s", err)
            window_area = window_data.get("area", 0.0)
            return WindowCalculationResult(
                power_total=0.0,
                power_direct=0.0,
                power_diffuse=0.0,
                power_direct_raw=0.0,
                power_diffuse_raw=0.0,
                power_total_raw=0.0,
                shadow_factor=1.0,
                is_visible=False,
                area_m2=window_area,
                shade_required=False,
                shade_reason=f"Validation error: {err}",
                effective_threshold=0.0,
            )
        except Exception as err:
            _LOGGER.exception("Unexpected error calculating solar power for window")
            window_area = window_data.get("area", 0.0)
            return WindowCalculationResult(
                power_total=0.0,
                power_direct=0.0,
                power_diffuse=0.0,
                power_direct_raw=0.0,
                power_diffuse_raw=0.0,
                power_total_raw=0.0,
                shadow_factor=1.0,
                is_visible=False,
                area_m2=window_area,
                shade_required=False,
                shade_reason=f"Calculation error: {err!r}",
                effective_threshold=0.0,
            )
        else:
            return result

    def _calculate_shadow_factor(  # noqa: PLR0913
        self,
        sun_elevation: float,
        sun_azimuth: float,
        window_azimuth: float,
        shadow_depth: float,
        shadow_offset: float,
        window_data: dict[str, Any] | None = None,
    ) -> float:
        """
        Calculate the geometric shadow factor for a window.

        Args:
            sun_elevation: Current sun elevation in degrees
            sun_azimuth: Current sun azimuth in degrees
            window_azimuth: Window azimuth in degrees
            shadow_depth: Depth of shadow element in meters
            shadow_offset: Vertical offset of shadow element in meters
            window_data: Window configuration data

        Returns:
            Shadow factor between 0.1 (full shadow) and 1.0 (no shadow)

        """
        # If no shadow geometry, return 1.0 (no shadow)
        if shadow_depth <= 0 and shadow_offset <= 0:
            return 1.0

        # Projected shadow length on the window plane
        # sun_elevation in degrees, convert to radians
        sun_trig = get_trig_values(sun_elevation)
        sun_el_rad = sun_trig["radians"]
        if sun_el_rad <= 0:
            return 1.0  # sun below horizon, no shadow

        # Calculate the angle difference between sun and window azimuth
        az_diff = ((sun_azimuth - window_azimuth + 180) % 360) - 180
        az_factor = max(
            0.0, get_trig_values(az_diff)["cos"]
        )  # 1.0 = direct, 0.0 = perpendicular

        # Shadow length: shadow_depth / tan(sun_elevation)
        try:
            shadow_length = shadow_depth / max(sun_trig["sin"] / sun_trig["cos"], 1e-3)
        except (ValueError, ZeroDivisionError):
            shadow_length = 0.0

        # Effective shadow on window: shadow_length - shadow_offset
        effective_shadow = max(0.0, shadow_length - shadow_offset)

        # Heuristic: if effective_shadow is large, strong shadow; if small, weak shadow
        # Get actual window height from window_data or fall back to default 1.0m
        wd = window_data or {}
        window_height = float(wd.get("window_height", 1.0))
        if effective_shadow <= 0:
            return 1.0  # no shadow
        if effective_shadow >= window_height:
            return 0.1  # full shadow (minimum factor)
        # Linear interpolation between 1.0 (no shadow) and 0.1 (full shadow)
        factor = 1.0 - 0.9 * (effective_shadow / window_height)
        # Angle dependency: more shadow if sun is direct, less if angled
        factor = factor * az_factor + (1.0 - az_factor)
        return max(0.1, min(1.0, factor))

    def _calculate_direct_power(
        self,
        params: dict[str, float],
        window_azimuth: float,
    ) -> float:
        """
        Calculate direct solar power component.

        Args:
            params: Dictionary containing solar parameters
            window_azimuth: Azimuth angle of the window in degrees

        Returns:
            Direct solar power in watts

        """
        sun_trig = get_trig_values(params["sun_elevation"])
        sun_az_trig = get_trig_values(params["sun_azimuth"])
        win_az_trig = get_trig_values(window_azimuth)
        tilt_trig = get_trig_values(params["tilt"])

        sun_el_rad = sun_trig["radians"]
        sun_az_rad = sun_az_trig["radians"]
        win_az_rad = win_az_trig["radians"]

        cos_incidence = sun_trig["sin"] * tilt_trig["cos"] + sun_trig[
            "cos"
        ] * tilt_trig["sin"] * math.cos(sun_az_rad - win_az_rad)
        if cos_incidence > 0 and sun_el_rad > 0:
            return (
                (
                    params["solar_radiation"]
                    * (1 - params["diffuse_factor"])
                    * cos_incidence
                    / sun_trig["sin"]
                )
                * params["area"]
                * params["g_value"]
            )
        return 0.0

    def _check_window_visibility(
        self,
        sun_elevation: float,
        sun_azimuth: float,
        window_data: dict[str, Any],
        effective_config: dict[str, Any] | None = None,
    ) -> tuple[bool, float]:
        """
        Check if sun is visible to window and return window azimuth.

        Args:
            sun_elevation: Current sun elevation in degrees
            sun_azimuth: Current sun azimuth in degrees
            window_data: Window configuration data
            effective_config: Effective configuration with inheritance resolved

        Returns:
            Tuple of (is_visible: bool, window_azimuth: float)

        """

        def safe_float(val: Any, default: float = 0.0) -> float:
            if val in ("", None, "inherit", "-1", -1):
                return default
            try:
                return float(val)
            except (ValueError, TypeError):
                return default

        # Use effective config if available, otherwise fall back to window_data
        config_source = effective_config if effective_config else window_data

        elevation_min = safe_float(config_source.get("elevation_min", 0), 0.0)
        elevation_max = safe_float(config_source.get("elevation_max", 90), 90.0)
        azimuth_min = safe_float(config_source.get("azimuth_min", -90), -90.0)
        azimuth_max = safe_float(config_source.get("azimuth_max", 90), 90.0)
        # Always get window_azimuth from window_data, not from config
        window_azimuth = safe_float(window_data.get("azimuth", 180), 180.0)

        is_visible = False
        if elevation_min <= sun_elevation <= elevation_max:
            # Calculate absolute visible azimuth range relative to window orientation
            # azimuth_min/max are relative angles to the window's azimuth
            visible_azimuth_min = window_azimuth + azimuth_min
            visible_azimuth_max = window_azimuth + azimuth_max

            # Check if sun is within the visible azimuth range
            if visible_azimuth_min <= sun_azimuth <= visible_azimuth_max:
                is_visible = True

        return is_visible, window_azimuth

    def _extract_calculation_parameters(
        self,
        effective_config: dict[str, Any],
        window_data: dict[str, Any],
        states: dict[str, Any],
    ) -> tuple[float, float, float, float, float, float, float, float, float]:
        """Extract and validate calculation parameters."""

        # Helper function for safe float conversion
        def safe_float(value: Any, default: float) -> float:
            """Safely convert value to float with fallback to default."""
            try:
                return float(value)
            except (ValueError, TypeError):
                return default

        # Extract solar radiation with safe conversion
        solar_radiation = safe_float(states.get("solar_radiation", 0.0), 0.0)

        # Extract sun position with safe conversion
        sun_elevation = safe_float(states.get("sun_elevation", 0.0), 0.0)
        sun_azimuth = safe_float(states.get("sun_azimuth", 180.0), 180.0)

        # Extract window parameters with safe conversion
        # Calculate area from dimensions if not explicitly provided
        if "area" in window_data:
            area = safe_float(window_data["area"], 1.0)
        else:
            window_width = safe_float(window_data.get("window_width", 1.0), 1.0)
            window_height = safe_float(window_data.get("window_height", 1.0), 1.0)
            frame_width = safe_float(
                effective_config.get("physical", {}).get("frame_width", 0.125), 0.125
            )
            glass_width = max(0, window_width - 2 * frame_width)
            glass_height = max(0, window_height - 2 * frame_width)
            area = glass_width * glass_height

        g_value = safe_float(window_data.get("g_value", 0.8), 0.8)
        tilt = safe_float(window_data.get("tilt", 90.0), 90.0)

        # Extract diffuse factor from config with safe conversion
        diffuse_factor = safe_float(effective_config.get("diffuse_factor", 0.3), 0.3)

        # Extract shadow parameters from window_data first, then effective_config
        shadow_depth = safe_float(
            window_data.get("shadow_depth", effective_config.get("shadow_depth", 0.0)),
            0.0,
        )
        shadow_offset = safe_float(
            window_data.get(
                "shadow_offset", effective_config.get("shadow_offset", 0.0)
            ),
            0.0,
        )

        return (
            solar_radiation,
            sun_azimuth,
            sun_elevation,
            g_value,
            diffuse_factor,
            tilt,
            area,
            shadow_depth,
            shadow_offset,
        )

    def _calculate_solar_power_direct(
        self,
        params: SolarCalculationParams | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> float:
        """
        Calculate direct solar power component.

        Args:
            params: SolarCalculationParams or dict with parameter keys. If a
                dict or kwargs are provided, missing fields will be filled with
                sensible defaults.
            **kwargs: Additional keyword parameters used when passing a dict
                rather than a SolarCalculationParams instance.

        Returns:
            Direct solar power in watts

        """
        # Accept either a SolarCalculationParams instance or a dict/kwargs
        if isinstance(params, SolarCalculationParams):
            p = params
        else:
            data: dict[str, Any] = {}
            if isinstance(params, dict):
                data.update(params)
            data.update(kwargs)
            # Build a SolarCalculationParams with defaults for missing fields
            p = SolarCalculationParams(
                solar_radiation=data.get("solar_radiation", 0.0),
                sun_elevation=data.get("sun_elevation", 0.0),
                sun_azimuth=data.get("sun_azimuth", 180.0),
                window_azimuth=data.get("window_azimuth", 180.0),
                area=data.get("area", 1.0),
                g_value=data.get("g_value", 0.8),
                tilt=data.get("tilt", 90.0),
                diffuse_factor=data.get("diffuse_factor", 0.3),
            )

        params_dict = {
            "solar_radiation": p.solar_radiation,
            "sun_elevation": p.sun_elevation,
            "sun_azimuth": p.sun_azimuth,
            "diffuse_factor": p.diffuse_factor,
            "tilt": p.tilt,
            "area": p.area,
            "g_value": p.g_value,
        }
        return self._calculate_direct_power(params_dict, p.window_azimuth)

    def _calculate_solar_power_diffuse(
        self,
        solar_radiation: float,
        diffuse_factor: float,
        area: float,
        g_value: float,
    ) -> float:
        """
        Calculate diffuse solar power component.

        Args:
            solar_radiation: Solar radiation in W/m²
            diffuse_factor: Fraction of diffuse radiation from configuration
            area: Window area in m² (glass area minus frames)
            g_value: Solar heat gain coefficient from configuration

        Returns:
            Diffuse solar power in watts

        """
        return solar_radiation * diffuse_factor * area * g_value

    def _calculate_total_solar_power(
        self,
        params: SolarCalculationParams | dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> float:
        """
        Calculate total solar power (direct + diffuse).

        Args:
            params: SolarCalculationParams or dict with parameter keys. If a
                dict or kwargs are provided, missing fields will be filled with
                sensible defaults.
            **kwargs: Additional keyword parameters used when passing a dict
                rather than a SolarCalculationParams instance.

        Returns:
            Total solar power in watts

        """
        # Reuse the flexible direct power wrapper
        if isinstance(params, SolarCalculationParams):
            p = params
        else:
            data: dict[str, Any] = {}
            if isinstance(params, dict):
                data.update(params)
            data.update(kwargs)
            p = SolarCalculationParams(
                solar_radiation=data.get("solar_radiation", 0.0),
                sun_elevation=data.get("sun_elevation", 0.0),
                sun_azimuth=data.get("sun_azimuth", 180.0),
                window_azimuth=data.get("window_azimuth", 180.0),
                area=data.get("area", 1.0),
                g_value=data.get("g_value", 0.8),
                tilt=data.get("tilt", 90.0),
                diffuse_factor=data.get("diffuse_factor", 0.3),
            )

        direct_power = self._calculate_solar_power_direct(p)
        diffuse_power = self._calculate_solar_power_diffuse(
            p.solar_radiation, p.diffuse_factor, p.area, p.g_value
        )
        return direct_power + diffuse_power

    def _calculate_power_per_square_meter(
        self,
        total_power: float,
        area: float = 1.0,
    ) -> float:
        """
        Calculate power per square meter.

        Args:
            total_power: Total power in watts
            area: Area in square meters (default: 1.0)

        Returns:
            Power per square meter in W/m²

        """
        if area <= 0:
            return 0.0
        return total_power / area

    def apply_global_factors(
        self, config: dict[str, Any], group_type: str, states: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Apply global sensitivity and offset factors to configuration.

        Robust gegen ungültige Werte.
        """
        # Schwellenwerte robust casten
        config["thresholds"]["direct"] = self._safe_float_conversion(  # type: ignore[attr-defined]
            config["thresholds"].get("direct", 200), 200
        )
        config["thresholds"]["diffuse"] = self._safe_float_conversion(  # type: ignore[attr-defined]
            config["thresholds"].get("diffuse", 150), 150
        )

        sensitivity = self._safe_float_conversion(  # type: ignore[attr-defined]
            states.get("sensitivity", 1.0), 1.0
        )
        config["thresholds"]["direct"] /= sensitivity
        config["thresholds"]["diffuse"] /= sensitivity

        if group_type == "children":
            factor = self._safe_float_conversion(  # type: ignore[attr-defined]
                states.get("children_factor", 1.0), 1.0
            )
            config["thresholds"]["direct"] *= factor
            config["thresholds"]["diffuse"] *= factor

        # Temperaturen robust casten
        config["temperatures"]["indoor_base"] = self._safe_float_conversion(  # type: ignore[attr-defined]
            config["temperatures"].get("indoor_base", 23.0), 23.0
        )
        config["temperatures"]["outdoor_base"] = self._safe_float_conversion(  # type: ignore[attr-defined]
            config["temperatures"].get("outdoor_base", 19.5), 19.5
        )

        temp_offset = self._safe_float_conversion(  # type: ignore[attr-defined]
            states.get("temperature_offset", 0.0), 0.0
        )
        config["temperatures"]["indoor_base"] += temp_offset
        config["temperatures"]["outdoor_base"] += temp_offset

        return config

    def _calculate_single_window(
        self,
        window_subentry_id: str,
        window_data: dict[str, Any],
        external_states: dict[str, Any],
    ) -> dict[str, Any]:
        """Calculate result for a single window."""
        try:
            # Get effective configuration and sources
            effective_config, effective_sources = self.get_effective_config_from_flows(  # type: ignore[attr-defined]
                window_subentry_id
            )

            # Apply global factors
            group_type = window_data.get("group_type", "default")
            effective_config = self.apply_global_factors(  # type: ignore[attr-defined]
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
            ) = self._get_scenario_enables_from_flows(  # type: ignore[attr-defined]
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
            shade_required, shade_reason = self._should_shade_window_from_flows(  # type: ignore[attr-defined]
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
            return self._get_error_window_result(  # type: ignore[attr-defined]
                window_data, window_subentry_id, err
            )

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
