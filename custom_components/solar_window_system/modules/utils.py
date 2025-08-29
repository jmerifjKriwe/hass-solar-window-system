"""
Utility functions and helpers.

This module contains general utility functions, data validation,
and common helper methods used across the solar window system.
"""

from __future__ import annotations

import logging
import math
from typing import Any

_LOGGER = logging.getLogger(__name__)


class UtilsMixin:
    """Mixin class for utility functionality."""

    def _validate_temperature_range(
        self, temp: float, min_temp: float = -50.0, max_temp: float = 60.0
    ) -> bool:
        """
        Validate temperature is within reasonable range.

        Args:
            temp: Temperature value to validate
            min_temp: Minimum acceptable temperature (default: -50.0°C)
            max_temp: Maximum acceptable temperature (default: 60.0°C)

        Returns:
            True if temperature is within range, False otherwise
        """
        if not isinstance(temp, (int, float)):
            _LOGGER.warning("Invalid temperature type: %s, expected number", type(temp))
            return False

        if math.isnan(temp) or math.isinf(temp):
            _LOGGER.warning("Invalid temperature value: %s", temp)
            return False

        if temp < min_temp:
            _LOGGER.warning(
                "Temperature %.1f°C below minimum threshold %.1f°C", temp, min_temp
            )
            return False

        if temp > max_temp:
            _LOGGER.warning(
                "Temperature %.1f°C above maximum threshold %.1f°C", temp, max_temp
            )
            return False

        return True

    def _safe_float_conversion(self, val: Any, default: float = 0.0) -> float:
        """
        Safely convert a value to float with robust error handling.

        Args:
            val: Value to convert
            default: Default value if conversion fails

        Returns:
            Float value or default
        """
        if val in ("", None, "inherit", "-1", -1):
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    def get_safe_state(
        self, hass: Any, entity_id: str, default: str | float = 0
    ) -> Any:
        """
        Safely get the state of an entity, returning a default if it is.

        unavailable, unknown, or not found.
        """
        if not entity_id:
            return default

        try:
            state = hass.states.get(entity_id)
        except (AttributeError, TypeError, KeyError) as e:
            _LOGGER.warning(
                "Error accessing entity %s: %s, returning default value.", entity_id, e
            )
            return default

        if state is None or state.state in ["unknown", "unavailable"]:
            _LOGGER.warning(
                "Entity %s not found or unavailable, returning default value.",
                entity_id,
            )
            return default

        return state.state

    def get_safe_attr(
        self, hass: Any, entity_id: str, attr: str, default: str | float = 0
    ) -> Any:
        """Safely get an attribute of an entity, returning a default if unavailable."""
        if not entity_id:
            return default

        try:
            state = hass.states.get(entity_id)
        except (AttributeError, TypeError, KeyError) as e:
            _LOGGER.warning(
                "Error accessing entity %s: %s, returning default value "
                "for attribute %s.",
                entity_id,
                e,
                attr,
            )
            return default

        if state is None or state.state in ["unknown", "unavailable"]:
            _LOGGER.warning(
                "Entity %s not found or unavailable, returning default value "
                "for attribute %s.",
                entity_id,
                attr,
            )
            return default

        return state.attributes.get(attr, default)

    def _format_debug_value(self, value: Any, precision: int = 2) -> str:
        """Format value for debug output with proper precision."""
        # Implementation will be moved from main calculator
        msg = "Implemented in main calculator"
        raise NotImplementedError(msg)

    def _calculate_time_difference_minutes(
        self, start_time: str, end_time: str
    ) -> float:
        """Calculate time difference in minutes between two time strings."""
        # Implementation will be moved from main calculator
        msg = "Implemented in main calculator"
        raise NotImplementedError(msg)

    def _is_valid_entity_state(self, state: Any) -> bool:
        """Check if entity state is valid (not None, not unknown)."""
        # Implementation will be moved from main calculator
        msg = "Implemented in main calculator"
        raise NotImplementedError(msg)
