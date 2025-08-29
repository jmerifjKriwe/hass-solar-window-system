"""
Flow-based integration and configuration handling.

This module contains flow-based configuration logic, inheritance handling,
and window calculation results.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
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

    def _get_subentries_by_type(self, entry_type: str) -> dict[str, Any]:
        """Get all config entries for a specific type."""
        msg = "Implemented in main calculator"
        raise NotImplementedError(msg)

    def get_effective_config_from_flows(
        self, window_subentry_id: str
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Get effective configuration using flow-based inheritance."""
        msg = "Implemented in main calculator"
        raise NotImplementedError(msg)

    def calculate_all_windows_from_flows(self) -> dict[str, Any]:
        """Calculate all window shading requirements using flow-based configuration."""
        msg = "Implemented in main calculator"
        raise NotImplementedError(msg)

    def _should_shade_window_from_flows(
        self, shade_request: ShadeRequestFlow
    ) -> tuple[bool, str]:
        """Flow-based shading decision with full scenario logic."""
        msg = "Implemented in main calculator"
        raise NotImplementedError(msg)

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

            if window_id in windows:
                return windows[window_id]

            _LOGGER.warning("Window %s not found in flow configuration", window_id)
            return {}

        except Exception:
            _LOGGER.exception("Error getting window config from flow for %s", window_id)
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

            if group_id in groups:
                return groups[group_id]

            _LOGGER.warning("Group %s not found in flow configuration", group_id)
            return {}

        except Exception:
            _LOGGER.exception("Error getting group config from flow for %s", group_id)
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

            # For global config, we typically expect a single entry or merged config
            if global_config:
                # If there's a specific global entry, return it
                if "global" in global_config:
                    return global_config["global"]
                # Otherwise return the first available config
                return next(iter(global_config.values()))

            _LOGGER.warning("No global configuration found in flow setup")
            return {}

        except Exception:
            _LOGGER.exception("Error getting global config from flow")
            return {}
