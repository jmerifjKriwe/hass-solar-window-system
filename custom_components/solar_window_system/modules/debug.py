"""
Debug functionality and entity search.

This module contains debug data creation and entity search functionality.
"""

from __future__ import annotations

from datetime import UTC, datetime
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.helpers import entity_registry as er

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class DebugMixin:
    """Mixin class for debug functionality."""

    # Type hint for hass attribute (provided by inheriting class)
    if TYPE_CHECKING:
        hass: HomeAssistant

    def create_debug_data(self, window_id: str) -> dict[str, Any] | None:
        """
        Create comprehensive debug data for a specific window.

        Args:
            window_id: The ID of the window to create debug data for

        Returns:
            Dictionary containing debug information or None if window not found

        """
        try:
            _LOGGER.debug("Creating debug data for window: %s", window_id)

            # Collect basic debug information using available methods
            debug_data = {
                "timestamp": datetime.now(UTC).isoformat(),
                "window_id": window_id,
                "current_sensor_states": self._collect_current_sensor_states(window_id),
                "window_sensors": self._search_window_sensors(self.hass, window_id),
                "global_sensors": self._search_global_sensors(self.hass),
            }

            # Try to get group sensors if window is in a group
            groups = {}  # This would need to be passed from main calculator
            debug_data["group_sensors"] = self._search_group_sensors(
                self.hass, window_id, groups
            )

            debug_data["calculation_steps"] = {
                "debug_data_collected": True,
                "window_sensors_found": len(debug_data["window_sensors"]),
                "global_sensors_found": len(debug_data["global_sensors"]),
                "group_sensors_found": len(debug_data["group_sensors"]),
            }

            _LOGGER.debug("Debug data created successfully for window: %s", window_id)

        except Exception as err:
            _LOGGER.exception("Error creating debug data for window %s", window_id)
            return {
                "timestamp": datetime.now(UTC).isoformat(),
                "window_id": window_id,
                "error": f"Debug data creation failed: {err!r}",
            }
        else:
            return debug_data

    def _collect_current_sensor_states(self, _window_id: str) -> dict[str, Any]:
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

    def _search_window_sensors(self, hass: Any, window_name: str) -> list[str]:
        """Search for window-level sensors."""
        try:
            # Get all sensor states
            all_states = hass.states.all()
            # Filter sensors that contain the window name
            window_sensors = [
                entity_id
                for entity_id, state in all_states
                if window_name.lower() in entity_id.lower()
            ]
            _LOGGER.debug(
                "Found %d sensors for window '%s'", len(window_sensors), window_name
            )
        except AttributeError:
            _LOGGER.exception("Error searching window sensors for '%s'", window_name)
            return []
        else:
            return window_sensors

    def _search_group_sensors(
        self, hass: Any, window_id: str, groups: dict[str, Any]
    ) -> list[str]:
        """Search for group-level sensors."""
        try:
            # Find which group contains this window
            window_group = None
            for group_name, group_data in groups.items():
                if "windows" in group_data and window_id in group_data["windows"]:
                    window_group = group_name
                    break

            if window_group:
                # Get all sensor states and filter for group sensors
                all_states = hass.states.all()
                group_sensors = [
                    entity_id
                    for entity_id, state in all_states
                    if window_group.lower() in entity_id.lower()
                ]
                _LOGGER.debug(
                    "Found %d sensors for group '%s' containing window '%s'",
                    len(group_sensors),
                    window_group,
                    window_id,
                )
                return group_sensors
            _LOGGER.debug("No group found containing window '%s'", window_id)
        except AttributeError:
            _LOGGER.exception(
                "Error searching group sensors for window '%s'", window_id
            )
            return []
        else:
            return []

    def _search_global_sensors(self, hass: Any) -> list[str]:
        """Search for global-level sensors."""
        try:
            # Get all sensor states and filter for global sensors
            all_states = hass.states.all()
            global_sensors = [
                entity_id
                for entity_id, state in all_states
                if "global" in entity_id.lower()
            ]
            _LOGGER.debug("Found %d global sensors", len(global_sensors))
        except AttributeError:
            _LOGGER.exception("Error searching global sensors")
            return []
        else:
            return global_sensors

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
