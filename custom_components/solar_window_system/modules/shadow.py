"""Shadow calculation module."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any


def get_trig_values(angle_deg: float) -> dict[str, float]:
    """
    Return trigonometric values for an angle in degrees.

    Local helper to avoid circular imports with the calculations module.
    """
    rad = math.radians(angle_deg)
    return {"radians": rad, "cos": math.cos(rad), "sin": math.sin(rad)}


@dataclass
class ShadowGeometry:
    """Parameters for shadow geometry calculations."""

    sun_elevation: float
    sun_azimuth: float
    window_azimuth: float
    shadow_depth: float
    shadow_offset: float
    # Require explicit window_height so callers must supply a value from
    # the effective configuration or window data. This avoids hidden
    # defaults that can lead to surprising results during tests.
    window_height: float


def calculate_shadow_factor(
    geometry: ShadowGeometry,
) -> float:
    """
    Calculate the geometric shadow factor for a window.

    Args:
        geometry: Parameters defining the shadow geometry

    Returns:
        A value between 0.1 (full shadow) and 1.0 (no shadow)

    """
    # If no shadow geometry, return 1.0 (no shadow)
    if geometry.shadow_depth <= 0 and geometry.shadow_offset <= 0:
        return 1.0

    # Projected shadow length on the window plane
    sun_trig = get_trig_values(geometry.sun_elevation)
    sun_el_rad = sun_trig["radians"]
    if sun_el_rad <= 0:
        return 1.0  # sun below horizon, no shadow

    # Calculate the angle difference between sun and window azimuth
    az_diff = ((geometry.sun_azimuth - geometry.window_azimuth + 180) % 360) - 180
    az_factor = max(0.0, get_trig_values(az_diff)["cos"])

    # Shadow length: shadow_depth / tan(sun_elevation)
    try:
        shadow_length = geometry.shadow_depth / max(
            sun_trig["sin"] / sun_trig["cos"], 1e-3
        )
    except (ValueError, ZeroDivisionError):
        shadow_length = 0.0

    # Effective shadow on window
    effective_shadow = max(0.0, shadow_length - geometry.shadow_offset)

    if effective_shadow <= 0:
        return 1.0  # no shadow
    if effective_shadow >= geometry.window_height:
        return 0.1  # full shadow (minimum factor)

    # Linear interpolation between 1.0 (no shadow) and 0.1 (full shadow)
    factor = 1.0 - 0.9 * (effective_shadow / geometry.window_height)
    # Angle dependency: more shadow if sun is direct, less if angled
    factor = factor * az_factor + (1.0 - az_factor)
    return max(0.1, min(1.0, factor))


def get_window_geometry(
    sun_elevation: float,
    sun_azimuth: float,
    window_data: dict[str, Any],
    effective_config: dict[str, Any] | None = None,
) -> ShadowGeometry:
    """
    Create shadow geometry parameters from window data and effective config.

    Args:
        sun_elevation: Sun elevation in degrees
        sun_azimuth: Sun azimuth in degrees
        window_data: Window configuration data
        effective_config: Optional effective configuration with inheritance resolved

    Returns:
        ShadowGeometry instance with all required parameters

    """
    # Use effective config if available, otherwise fall back to window_data
    config = effective_config if effective_config else window_data

    # Get window parameters with safe defaults
    window_height = float(window_data.get("window_height", 1.0))
    window_azimuth = float(window_data.get("azimuth", 180.0))

    # Get shadow parameters with config fallback
    shadow_depth = float(
        window_data.get("shadow_depth", config.get("shadow_depth", 0.0))
    )
    shadow_offset = float(
        window_data.get("shadow_offset", config.get("shadow_offset", 0.0))
    )

    return ShadowGeometry(
        sun_elevation=sun_elevation,
        sun_azimuth=sun_azimuth,
        window_azimuth=window_azimuth,
        shadow_depth=shadow_depth,
        shadow_offset=shadow_offset,
        window_height=window_height,
    )
