"""
Shading decision logic and scenario handling.

This module contains all shading decision logic, scenario evaluation,
and shade requirement determination.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .flow_integration import ShadeRequestFlow

_LOGGER = logging.getLogger(__name__)


class ShadingMixin:
    """Mixin class for shading decision functionality."""

    def _should_shade_window_from_flows(
        self, shade_request: ShadeRequestFlow
    ) -> tuple[bool, str]:
        """Flow-based shading decision with full scenario logic."""
        msg = "Implemented in main calculator"
        raise NotImplementedError(msg)

    def _evaluate_shading_scenarios(
        self,
        shade_request: ShadeRequestFlow,
        indoor_temp: float,
        outdoor_temp: float,
    ) -> tuple[bool, str]:
        """Evaluate all shading scenarios and return the result."""
        msg = "Implemented in main calculator"
        raise NotImplementedError(msg)

    def _check_scenario_b(
        self,
        shade_request: ShadeRequestFlow,
        scenario_b_config: dict[str, Any],
        indoor_temp: float,
        outdoor_temp: float,
    ) -> tuple[bool, str]:
        """Check scenario B: Diffuse heat."""
        msg = "Implemented in main calculator"
        raise NotImplementedError(msg)

    def _check_scenario_c(
        self,
        shade_request: ShadeRequestFlow,
        indoor_temp: float,
    ) -> tuple[bool, str]:
        """Check scenario C: Heatwave forecast."""
        msg = "Implemented in main calculator"
        raise NotImplementedError(msg)

    def _get_scenario_enables_from_flows(
        self,
        window_subentry_id: str,
        global_states: dict[str, Any],
    ) -> tuple[bool, bool]:
        """Get scenario B and C enables with flow-based inheritance logic."""
        msg = "Implemented in main calculator"
        raise NotImplementedError(msg)
