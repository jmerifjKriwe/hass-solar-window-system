"""
Caching functionality for entity states.

This module contains caching logic for entity states to improve performance.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class UtilsProtocol(Protocol):
    """Protocol for classes that provide utility methods."""

    def get_safe_state(self, entity_id: str, default_value: Any | None = None) -> Any:
        """Get entity state safely with fallback."""
        ...


class CacheMixin:
    """Mixin class for caching functionality."""

    # Type hint for hass attribute (provided by inheriting class)
    if TYPE_CHECKING:
        hass: HomeAssistant

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the CacheMixin with cache attributes."""
        super().__init__(*args, **kwargs)
        self._entity_cache: dict[str, Any] = {}
        self._cache_timestamp: float | None = None
        self._cache_ttl = 30  # 30 seconds cache for one calculation run

    def _get_cached_entity_state(
        self, entity_id: str, default_value: Any | None = None
    ) -> Any:
        """
        Get entity state with short-term caching for one calculation run.

        With debug logging.
        """
        current_time = time.time()

        # Check if cache is expired
        if (
            self._cache_timestamp is None
            or current_time - self._cache_timestamp > self._cache_ttl
        ):
            self._entity_cache.clear()
            self._cache_timestamp = current_time

        # Check cache first
        if entity_id in self._entity_cache:
            value = self._entity_cache[entity_id]
        else:
            # Get from HomeAssistant using get_safe_state for better error handling
            try:
                loop = asyncio.get_running_loop()
                value = loop.run_until_complete(
                    self.hass.async_add_executor_job(
                        self.get_safe_state,  # type: ignore[attr-defined]
                        entity_id,
                        default_value,
                    )
                )
            except RuntimeError:
                # No running loop, use synchronous call
                value = self.get_safe_state(entity_id, default_value)  # type: ignore[attr-defined]
            # Cache the result
            self._entity_cache[entity_id] = value
        return value

    def _resolve_entity_state_with_fallback(
        self, entity_id: str, fallback: str, valid_states: set[str]
    ) -> str:
        """Resolve entity state with validation and fallback."""
        state = self._get_cached_entity_state(entity_id, fallback)
        if state in valid_states:
            return state
        _LOGGER.warning(
            "Invalid state '%s' for entity %s, using fallback '%s'",
            state,
            entity_id,
            fallback,
        )
        return fallback
