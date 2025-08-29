"""
Debug functionality and entity search.

This module contains debug data creation and entity search functionality.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.helpers import entity_registry as er

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class DebugMixin:
    """Mixin class for debug functionality."""

    def create_debug_data(self, window_id: str) -> dict[str, Any] | None:
        """Create comprehensive debug data for a specific window."""
        # Implementation will be moved from main calculator
        raise NotImplementedError("Implemented in main calculator")

    def _collect_current_sensor_states(self, window_id: str) -> dict[str, Any]:
        """
        Collect current states of all Solar Window System sensors.

        Args:
            window_id: Window identifier for context

        Returns:
            Dictionary with current sensor states
        """
        sensor_states = {}

        try:
            # Get entity registry
            entity_reg = er.async_get(self.hass)

            # Collect all SWS sensor states
            for entity_id, entity_entry in entity_reg.entities.items():
                if entity_id.startswith("sensor.sws_"):
                    try:
                        state = self.hass.states.get(entity_id)
                        if state:
                            sensor_states[entity_id] = {
                                "state": state.state,
                                "name": entity_entry.name,
                                "last_updated": (
                                    state.last_updated.isoformat()
                                    if state.last_updated
                                    else None
                                ),
                                "attributes": (
                                    dict(state.attributes) if state.attributes else {}
                                ),
                            }
                    except (AttributeError, KeyError) as e:
                        _LOGGER.warning("Error getting state for %s: %s", entity_id, e)
                        sensor_states[entity_id] = {
                            "state": "unavailable",
                            "name": entity_entry.name,
                            "error": str(e),
                        }

        except Exception:
            _LOGGER.exception("Error collecting sensor states")

        return sensor_states

    def _get_current_sensor_states(self, window_id: str) -> dict[str, Any]:
        """
        Get current states of all Solar Window System sensors.

        Args:
            window_id: Window identifier for context

        Returns:
            Dictionary with current sensor states
        """
        # This is an alias for _collect_current_sensor_states for backward compatibility
        return self._collect_current_sensor_states(window_id)

    def _generate_debug_output(self, sensor_states: dict[str, Any]) -> str:
        """
        Generate formatted debug output from sensor states.

        Args:
            sensor_states: Dictionary of sensor states

        Returns:
            Formatted debug output string
        """
        if not sensor_states:
            return "No sensor states available"

        output_lines = ["Solar Window System Debug Output:", "=" * 40]

        for entity_id, state_info in sensor_states.items():
            output_lines.append(f"Entity: {entity_id}")
            output_lines.append(f"  State: {state_info.get('state', 'unknown')}")
            if "name" in state_info:
                output_lines.append(f"  Name: {state_info['name']}")
            if "error" in state_info:
                output_lines.append(f"  Error: {state_info['error']}")
            output_lines.append("")

        return "\n".join(output_lines)

    def _search_window_sensors(
        self, sensor_states: dict[str, Any], window_name: str
    ) -> None:
        """Search for window-level sensors."""
        msg = "Implemented in main calculator"
        raise NotImplementedError(msg)

    def _search_group_sensors(
        self, sensor_states: dict[str, Any], window_id: str, groups: dict[str, Any]
    ) -> None:
        """Search for group-level sensors."""
        msg = "Implemented in main calculator"
        raise NotImplementedError(msg)

    def _search_global_sensors(self, sensor_states: dict[str, Any]) -> None:
        """Search for global-level sensors."""
        msg = "Implemented in main calculator"
        raise NotImplementedError(msg)

    def _find_entity_by_name(
        self,
        hass: Any,
        entity_name: str,
        entity_type: str = "global",
        window_name: str | None = None,
        group_name: str | None = None,
    ) -> str | None:
        """
        Find entity ID by entity name with Solar Window System specific search.

        Args:
            hass: Home Assistant instance
            entity_name: The name of the entity to find
            entity_type: Type of entity ("window", "group", "global")
            window_name: Window name for window-specific entities
            group_name: Group name for group-specific entities

        Returns:
            Entity ID if found, None otherwise

        """
        try:
            # Get entity registry
            entity_reg = er.async_get(hass)

            # Build expected entity ID patterns based on type
            expected_patterns = []
            sensor_key = (
                entity_name.lower()
                .replace("/", "_")
                .replace(" ", "_")
                .replace("²", "2")
            )

            if entity_type == "window" and window_name:
                # Window-specific patterns
                expected_patterns = [
                    f"sensor.sws_window_{window_name}_{sensor_key}",
                    f"sensor.sws_window_{window_name.lower()}_{sensor_key}",
                ]
            elif entity_type == "group" and group_name:
                # Group-specific patterns
                expected_patterns = [
                    f"sensor.sws_group_{group_name}_{sensor_key}",
                    f"sensor.sws_group_{group_name.lower()}_{sensor_key}",
                ]
            else:
                # Global patterns
                expected_patterns = [
                    f"sensor.sws_global_{sensor_key}",
                    f"sensor.sws_{sensor_key}",
                ]

            # First try: Search for exact entity ID matches
            for pattern in expected_patterns:
                if pattern in entity_reg.entities:
                    entity_entry = entity_reg.entities[pattern]
                    if entity_entry.name == entity_name:
                        return pattern

            # Second try: Search by name but filter for SWS entities only
            for entity_id, entity_entry in entity_reg.entities.items():
                if entity_entry.name == entity_name and entity_id.startswith(
                    "sensor.sws_"
                ):
                    # Additional validation based on type
                    if (
                        entity_type == "window"
                        and window_name
                        and (
                            f"window_{window_name}" in entity_id
                            or f"window_{window_name.lower()}" in entity_id
                        )
                    ):
                        return entity_id
                    if (
                        entity_type == "group"
                        and group_name
                        and (
                            f"group_{group_name}" in entity_id
                            or f"group_{group_name.lower()}" in entity_id
                        )
                    ):
                        return entity_id
                    if entity_type == "global" and (
                        "global" in entity_id
                        or not any(x in entity_id for x in ["window_", "group_"])
                    ):
                        return entity_id

        except Exception:
            _LOGGER.exception(
                "Error finding entity by name '%s' (type: %s)", entity_name, entity_type
            )

        return None
