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
        """Safely get the state of an entity, returning a default if unavailable."""
        if not entity_id:
            return default

        if not hasattr(hass, "states") or not hasattr(hass.states, "get"):
            _LOGGER.error(
                "Invalid hass object passed to get_safe_state: %s (type: %s)",
                hass,
                type(hass),
            )
            return default

        try:
            state = hass.states.get(entity_id)
        except (AttributeError, TypeError, KeyError) as e:
            _LOGGER.warning(
                "Error accessing entity %s: %s, returning default value.", entity_id, e
            )
            return default

        if state is None or getattr(state, "state", None) in ["unknown", "unavailable"]:
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

        if not hasattr(hass, "states") or not hasattr(hass.states, "get"):
            _LOGGER.error(
                "Invalid hass object passed to get_safe_attr: %s (type: %s)",
                hass,
                type(hass),
            )
            return default

        try:
            state = hass.states.get(entity_id)
        except (AttributeError, TypeError, KeyError) as e:
            _LOGGER.warning(
                "Error accessing entity %s: %s, returning default for attr %s.",
                entity_id,
                e,
                attr,
            )
            return default

        if state is None or getattr(state, "state", None) in ["unknown", "unavailable"]:
            _LOGGER.warning(
                "Entity %s not found or unavailable, default for attr %s.",
                entity_id,
                attr,
            )
            return default

        # Handle attributes - check if it's a dict-like object
        value = default
        try:
            if hasattr(state, "attributes"):
                # Handle both real dicts and Mock objects
                if hasattr(state.attributes, "get") and callable(state.attributes.get):
                    value = state.attributes.get(attr, default)
                elif hasattr(state.attributes, attr):
                    value = getattr(state.attributes, attr, default)
        except (AttributeError, TypeError, KeyError):
            pass
        return value

    def _format_debug_value(self, value: Any, precision: int = 2) -> str:
        """Format value for debug output with proper precision."""
        if value is None:
            return "None"
        if isinstance(value, (int, float)):
            return f"{value:.{precision}f}"
        if isinstance(value, bool):
            return "True" if value else "False"
        return str(value)

    def _calculate_time_difference_minutes(
        self, start_time: str, end_time: str
    ) -> float:
        """Calculate time difference in minutes between two time strings."""
        try:
            # Parse time strings (assuming HH:MM format)
            start_hour, start_min = map(int, start_time.split(":"))
            end_hour, end_min = map(int, end_time.split(":"))

            # Convert to minutes
            start_minutes = start_hour * 60 + start_min
            end_minutes = end_hour * 60 + end_min

            # Handle overnight time differences
            if end_minutes < start_minutes:
                end_minutes += 24 * 60  # Add 24 hours

            return float(end_minutes - start_minutes)
        except (ValueError, AttributeError):
            _LOGGER.warning("Invalid time format: %s to %s", start_time, end_time)
            return 0.0

    def _is_valid_entity_state(self, state: Any) -> bool:
        """Check if entity state is valid (not None, not unknown)."""
        if state is None:
            return False
        state_value = state.state if hasattr(state, "state") else state

        # Check for invalid states
        invalid_states = ["unknown", "unavailable", None, ""]
        return state_value not in invalid_states
