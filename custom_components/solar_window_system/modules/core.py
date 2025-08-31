"""
Core Solar Window Calculator functionality.

This module contains the main SolarWindowCalculator class and basic functionality.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any

from .calculations import CalculationsMixin
from .debug import DebugMixin
from .flow_integration import FlowIntegrationMixin
from .utils import UtilsMixin

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .flow_integration import WindowCalculationResult

_LOGGER = logging.getLogger(__name__)


class SolarWindowCalculator(
    CalculationsMixin,
    DebugMixin,
    FlowIntegrationMixin,
    UtilsMixin,
):
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

        # Flow-based attributes - will be set by __init_flow_based__
        self.global_entry = None

        # Entity cache for performance
        self._entity_cache: dict[str, Any] = {}
        self._entity_cache_timestamps: dict[str, float] = {}
        self._cache_timestamp: float | None = None
        self._cache_ttl = 30  # seconds

        # LRU cache for entity states (max 100 entries)
        self._lru_cache: dict[str, tuple[Any, float]] = {}
        self._lru_max_size = 100

    async def _get_lru_cached_entity_state_async(self, entity_id: str) -> Any:
        """Get entity state with LRU caching (async version)."""
        current_time = time.time()

        # Check LRU cache first
        if entity_id in self._lru_cache:
            value, timestamp = self._lru_cache[entity_id]
            if current_time - timestamp < self._cache_ttl:
                return value
            # Expired, remove from cache
            del self._lru_cache[entity_id]

        # Get fresh value asynchronously
        try:
            # Use thread executor to avoid blocking event loop
            loop = asyncio.get_event_loop()
            state = await loop.run_in_executor(None, self.hass.states.get, entity_id)
            value = state.state if state else None
        except (AttributeError, KeyError, TypeError):
            value = None

        # Add to LRU cache
        if len(self._lru_cache) >= self._lru_max_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._lru_cache))
            del self._lru_cache[oldest_key]

        self._lru_cache[entity_id] = (value, current_time)
        return value

    def _get_lru_cached_entity_state(self, entity_id: str) -> Any:
        """Get entity state with LRU caching (synchronous version)."""
        current_time = time.time()

        # Check LRU cache first
        if entity_id in self._lru_cache:
            value, timestamp = self._lru_cache[entity_id]
            if current_time - timestamp < self._cache_ttl:
                return value
            # Expired, remove from cache
            del self._lru_cache[entity_id]

        # Get fresh value synchronously
        try:
            state = self.hass.states.get(entity_id)
            value = state.state if state else None
        except (AttributeError, KeyError, TypeError):
            value = None

        # Add to LRU cache
        if len(self._lru_cache) >= self._lru_max_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._lru_cache))
            del self._lru_cache[oldest_key]

        self._lru_cache[entity_id] = (value, current_time)
        return value

    def get_safe_state(self, entity_id: str, default: Any = 0) -> Any:
        """Get entity state safely with fallback (synchronous version)."""
        value = self._get_lru_cached_entity_state(entity_id)
        return value if value is not None else default

    def get_safe_attr(self, entity_id: str, attr: str, default: str | float = 0) -> Any:
        """Get entity attribute safely with fallback."""
        return super().get_safe_attr(self.hass, entity_id, attr, default)

    async def get_safe_attr_async(
        self, entity_id: str, attr: str, default: str | float = 0
    ) -> Any:
        """Get entity attribute safely with fallback (async version)."""
        try:
            # Use thread executor for attribute access to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, super().get_safe_attr, self.hass, entity_id, attr, default
            )
        except (AttributeError, KeyError, TypeError):
            return default

    def _get_cached_entity_state(
        self, entity_id: str, default_value: Any | None = None
    ) -> Any:
        """Get cached entity state with smart TTL invalidation."""
        current_time = time.time()

        # Always check for expired entries and clean them up
        # Remove expired entries from LRU cache
        expired_lru_keys = [
            key
            for key, (_, timestamp) in self._lru_cache.items()
            if current_time - timestamp > self._cache_ttl
        ]
        for key in expired_lru_keys:
            del self._lru_cache[key]
            # Also remove from entity cache if present
            if key in self._entity_cache:
                del self._entity_cache[key]

        # Remove expired entries from entity cache based on timestamps
        if hasattr(self, "_entity_cache_timestamps"):
            expired_entity_keys = [
                key
                for key, timestamp in self._entity_cache_timestamps.items()
                if current_time - timestamp > self._cache_ttl
            ]
            for key in expired_entity_keys:
                if key in self._entity_cache:
                    del self._entity_cache[key]
                del self._entity_cache_timestamps[key]

        # Update cache timestamp
        self._cache_timestamp = current_time

        # Return cached value if available (and not expired)
        if entity_id in self._entity_cache:
            return self._entity_cache[entity_id]

        # Get fresh value and cache it (bypass LRU cache)
        try:
            state = self.hass.states.get(entity_id)
            value = state.state if state else default_value
        except (AttributeError, KeyError, TypeError):
            value = default_value
        self._entity_cache[entity_id] = value

        # Initialize timestamps dict if it doesn't exist
        if not hasattr(self, "_entity_cache_timestamps"):
            self._entity_cache_timestamps = {}
        self._entity_cache_timestamps[entity_id] = current_time

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
        """
        Calculate solar power for a window including shadow effects.

        Uses the modular CalculationsMixin implementation.
        """
        return super().calculate_window_solar_power_with_shadow(
            effective_config, window_data, states
        )

    def create_debug_data(self, window_id: str) -> dict[str, Any] | None:
        """
        Create comprehensive debug data for a specific window.

        Uses the modular DebugMixin implementation.
        """
        return super().create_debug_data(window_id)

    def calculate_all_windows_from_flows(self) -> dict[str, Any]:
        """
        Calculate all window shading requirements using flow-based configuration.

        Uses the modular FlowIntegrationMixin implementation.
        """
        return super().calculate_all_windows_from_flows()
