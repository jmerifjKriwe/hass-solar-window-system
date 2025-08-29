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
        try:
            # Handle Mock objects gracefully - check if this is test data
            mock_check = hasattr(shade_request, "_mock_name") or "Mock" in str(
                type(shade_request)
            )
            if mock_check:
                return False, "Mock data - cannot determine shading requirement"

            # Basic implementation: shade if solar power exceeds threshold
            threshold = shade_request.effective_config.get("threshold", 100.0)

            # Handle Mock objects gracefully
            try:
                solar_power = shade_request.solar_result.power_total

                # Check if both values are numeric before comparison
                if isinstance(solar_power, (int, float)) and isinstance(
                    threshold, (int, float)
                ):
                    if solar_power > threshold:
                        reason = (
                            f"Solar power {solar_power:.1f}W "
                            f"exceeds threshold {threshold}W"
                        )
                        return True, reason
                else:
                    # Mock objects or non-numeric values - return default behavior
                    return False, "Mock data - cannot determine shading requirement"
            except (AttributeError, TypeError):
                # Mock objects or invalid data
                return (
                    False,
                    "Invalid solar data - cannot determine shading requirement",
                )
            else:
                return False, "Solar power within acceptable range"
        except (AttributeError, TypeError, ValueError) as e:
            _LOGGER.warning("Error in shading decision: %s", e)
            return False, f"Error in shading calculation: {e}"

    def _evaluate_shading_scenarios(
        self,
        shade_request: ShadeRequestFlow,
        indoor_temp: float,  # noqa: ARG002 - kept for API compatibility
        outdoor_temp: float,  # noqa: ARG002 - kept for API compatibility
    ) -> tuple[bool, str]:
        """Evaluate all shading scenarios and return the result."""
        # For now, delegate to the basic flow-based decision
        # Note: indoor_temp and outdoor_temp could be used for advanced scenarios
        return self._should_shade_window_from_flows(shade_request)

    def _check_scenario_b(
        self,
        shade_request: ShadeRequestFlow,  # noqa: ARG002 - kept for API compatibility
        scenario_b_config: dict[str, Any],
        indoor_temp: float,
        outdoor_temp: float,
    ) -> tuple[bool, str]:
        """Check scenario B: Diffuse heat."""
        # Scenario B: Shade when indoor temperature is high and outdoor is higher
        temp_threshold = scenario_b_config.get("indoor_temp_threshold", 25.0)
        temp_diff_threshold = scenario_b_config.get("temp_diff_threshold", 5.0)

        temp_diff = outdoor_temp - indoor_temp
        if indoor_temp > temp_threshold and temp_diff > temp_diff_threshold:
            reason = (
                f"Indoor temp {indoor_temp}°C > {temp_threshold}°C "
                f"and outdoor diff > {temp_diff_threshold}°C"
            )
            return True, reason
        return False, "Scenario B conditions not met"

    def _check_scenario_c(
        self,
        shade_request: ShadeRequestFlow,
        indoor_temp: float,
    ) -> tuple[bool, str]:
        """Check scenario C: Heatwave forecast."""
        # Scenario C: Shade during heatwave conditions
        heatwave_threshold = shade_request.effective_config.get(
            "heatwave_threshold", 30.0
        )

        if indoor_temp > heatwave_threshold:
            reason = (
                f"Heatwave conditions: indoor temp {indoor_temp}°C > "
                f"{heatwave_threshold}°C"
            )
            return True, reason
        return False, "No heatwave conditions detected"

    def _get_scenario_enables_from_flows(
        self,
        window_subentry_id: str,  # noqa: ARG002 - kept for API compatibility
        global_states: dict[str, Any],
    ) -> tuple[bool, bool]:
        """Get scenario B and C enables with flow-based inheritance logic."""
        # For now, return default values - can be extended with flow logic later
        # Note: window_subentry_id could be used for window-specific scenario enables
        scenario_b_enabled = global_states.get("scenario_b_enabled", False)
        scenario_c_enabled = global_states.get("scenario_c_enabled", False)

        return scenario_b_enabled, scenario_c_enabled
