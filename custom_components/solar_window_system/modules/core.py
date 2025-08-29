"""
Core Solar Window Calculator functionality.

This module contains the main SolarWindowCalculator class and basic functionality.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .flow_integration import WindowCalculationResult

_LOGGER = logging.getLogger(__name__)


class SolarWindowCalculator:
    """
    Main calculator class for Solar Window System calculations.

    This class handles the core calculation logic and coordinates
    between different calculation modules.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        defaults_config: dict[str, Any] | None = None,
        groups_config: dict[str, Any] | None = None,
        windows_config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the calculator."""
        self.hass = hass
        self.defaults_config = defaults_config or {}
        self.groups_config = groups_config or {}
        self.windows_config = windows_config or {}

        # Entity cache for performance
        self._entity_cache: dict[str, Any] = {}
        self._cache_timestamp: float | None = None
        self._cache_ttl = 30  # seconds

        # Global entry reference (set by coordinator)
        self.global_entry: Any = None

    def get_safe_state(self, entity_id: str, default: Any = 0) -> Any:
        """Get entity state safely with fallback."""
        try:
            state = self.hass.states.get(entity_id)
        except (AttributeError, KeyError, TypeError):
            return default
        else:
            return state.state if state else default

    def get_safe_attr(self, entity_id: str, attr: str, default: str | float = 0) -> Any:
        """Get entity attribute safely with fallback."""
        try:
            state = self.hass.states.get(entity_id)
            return getattr(state, attr, default) if state else default
        except (AttributeError, KeyError, TypeError):
            return default

    def _get_cached_entity_state(
        self, entity_id: str, default_value: Any | None = None
    ) -> Any:
        """Get cached entity state with TTL."""
        current_time = time.time()

        # Check if cache is still valid
        if (
            self._cache_timestamp is None
            or current_time - self._cache_timestamp > self._cache_ttl
        ):
            self._entity_cache.clear()
            self._cache_timestamp = current_time

        # Return cached value if available
        if entity_id in self._entity_cache:
            return self._entity_cache[entity_id]

        # Get fresh value and cache it
        value = self.get_safe_state(entity_id, default_value)
        self._entity_cache[entity_id] = value
        return value

    def _resolve_entity_state_with_fallback(
        self, entity_id: str, fallback: str, valid_states: set[str]
    ) -> str:
        """Resolve entity state with fallback logic."""
        if not entity_id:
            return fallback

        state = self._get_cached_entity_state(entity_id, fallback)
        return state if state in valid_states else fallback

    # Placeholder for methods that will be implemented in other modules
    def calculate_window_solar_power_with_shadow(
        self,
        effective_config: dict[str, Any],
        window_data: dict[str, Any],
        states: dict[str, Any],
    ) -> WindowCalculationResult:
        """Calculate solar power for a window including shadow effects."""
        # This will be implemented in calculations.py
        msg = "Implemented in calculations module"
        raise NotImplementedError(msg)

    def create_debug_data(self, window_id: str) -> dict[str, Any] | None:
        """Create comprehensive debug data for a specific window."""
        # This will be implemented in debug.py
        msg = "Implemented in debug module"
        raise NotImplementedError(msg)

    def calculate_all_windows_from_flows(self) -> dict[str, Any]:
        """Calculate all window shading requirements using flow-based configuration."""
        # This will be implemented in flow_integration.py
        msg = "Implemented in flow_integration module"
        raise NotImplementedError(msg)
