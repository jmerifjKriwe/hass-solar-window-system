"""
Solar power calculations and physical computations.

This module contains all solar power calculation logic, shadow calculations,
and physical parameter handling.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import math
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .flow_integration import WindowCalculationResult

_LOGGER = logging.getLogger(__name__)


@dataclass
class SolarCalculationParams:
    """Parameters for solar power calculations."""

    solar_radiation: float
    sun_elevation: float
    sun_azimuth: float
    window_azimuth: float = 180.0
    area: float = 1.0
    g_value: float = 0.8
    tilt: float = 90.0
    diffuse_factor: float = 0.3


class CalculationsMixin:
    """Mixin class for calculation functionality."""

    def calculate_window_solar_power_with_shadow(
        self,
        effective_config: dict[str, Any],
        window_data: dict[str, Any],
        states: dict[str, Any],
    ) -> WindowCalculationResult:
        """Calculate solar power for a window including shadow effects."""
        # Implementation will be moved from main calculator
        msg = "Implemented in main calculator"
        raise NotImplementedError(msg)

    def _calculate_shadow_factor(
        self,
        sun_elevation: float,
        sun_azimuth: float,
        window_azimuth: float,
        shadow_depth: float,
        shadow_offset: float,
    ) -> float:
        """
        Calculate the geometric shadow factor for a window.

        Returns a value between 0.1 (full shadow) and 1.0 (no shadow).
        """
        # If no shadow geometry, return 1.0 (no shadow)
        if shadow_depth <= 0 and shadow_offset <= 0:
            return 1.0

        # Projected shadow length on the window plane
        # sun_elevation in degrees, convert to radians
        sun_el_rad = math.radians(sun_elevation)
        if sun_el_rad <= 0:
            return 1.0  # sun below horizon, no shadow

        # Calculate the angle difference between sun and window azimuth
        az_diff = ((sun_azimuth - window_azimuth + 180) % 360) - 180
        az_factor = max(
            0.0, math.cos(math.radians(az_diff))
        )  # 1.0 = direct, 0.0 = perpendicular

        # Shadow length: shadow_depth / tan(sun_elevation)
        try:
            shadow_length = shadow_depth / max(math.tan(sun_el_rad), 1e-3)
        except (ValueError, ZeroDivisionError):
            shadow_length = 0.0

        # Effective shadow on window: shadow_length - shadow_offset
        effective_shadow = max(0.0, shadow_length - shadow_offset)

        # Heuristic: if effective_shadow is large, strong shadow; if small, weak shadow
        # For simplicity, assume window height = 1.0m (normalized)
        window_height = 1.0
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
        sun_el_rad = math.radians(params["sun_elevation"])
        sun_az_rad = math.radians(params["sun_azimuth"])
        win_az_rad = math.radians(window_azimuth)
        tilt_rad = math.radians(params["tilt"])

        cos_incidence = math.sin(sun_el_rad) * math.cos(tilt_rad) + math.cos(
            sun_el_rad
        ) * math.sin(tilt_rad) * math.cos(sun_az_rad - win_az_rad)

        if cos_incidence > 0 and sun_el_rad > 0:
            return (
                (
                    params["solar_radiation"]
                    * (1 - params["diffuse_factor"])
                    * cos_incidence
                    / math.sin(sun_el_rad)
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
        window_azimuth = safe_float(config_source.get("azimuth", 180), 180.0)

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
        msg = "Implemented in main calculator"
        raise NotImplementedError(msg)

    def _calculate_solar_power_direct(
        self,
        params: SolarCalculationParams,
    ) -> float:
        """
        Calculate direct solar power component.

        Args:
            params: Solar calculation parameters

        Returns:
            Direct solar power in watts

        """
        # Use the existing _calculate_direct_power method with proper parameters
        params_dict = {
            "solar_radiation": params.solar_radiation,
            "sun_elevation": params.sun_elevation,
            "sun_azimuth": params.sun_azimuth,
            "diffuse_factor": params.diffuse_factor,
            "tilt": params.tilt,
            "area": params.area,
            "g_value": params.g_value,
        }
        return self._calculate_direct_power(params_dict, params.window_azimuth)

    def _calculate_solar_power_diffuse(
        self,
        solar_radiation: float,
        diffuse_factor: float = 0.3,
        area: float = 1.0,
        g_value: float = 0.8,
    ) -> float:
        """
        Calculate diffuse solar power component.

        Args:
            solar_radiation: Solar radiation in W/m²
            diffuse_factor: Fraction of diffuse radiation (default: 0.3)
            area: Window area in m² (default: 1.0)
            g_value: Solar heat gain coefficient (default: 0.8)

        Returns:
            Diffuse solar power in watts

        """
        return solar_radiation * diffuse_factor * area * g_value

    def _calculate_total_solar_power(
        self,
        solar_radiation: float,
        diffuse_factor: float = 0.3,
        area: float = 1.0,
        g_value: float = 0.8,
    ) -> float:
        """
        Calculate total solar power (direct + diffuse).

        Args:
            solar_radiation: Solar radiation in W/m²
            diffuse_factor: Fraction of diffuse radiation (default: 0.3)
            area: Window area in m² (default: 1.0)
            g_value: Solar heat gain coefficient (default: 0.8)

        Returns:
            Total solar power in watts

        """
        # Total power = direct + diffuse
        params = SolarCalculationParams(
            solar_radiation=solar_radiation,
            sun_elevation=45.0,  # Default values for simple calculation
            sun_azimuth=180.0,
            area=area,
            g_value=g_value,
            diffuse_factor=diffuse_factor,
        )
        direct_power = self._calculate_solar_power_direct(params)
        diffuse_power = self._calculate_solar_power_diffuse(
            solar_radiation, diffuse_factor, area, g_value
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
