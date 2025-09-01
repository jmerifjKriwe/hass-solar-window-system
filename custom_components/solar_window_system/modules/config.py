"""
Configuration handling and inheritance logic.

This module contains configuration merging, inheritance, and flow-based config logic.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class ConfigMixin:
    """Mixin class for configuration functionality."""

    # Type hint for hass attribute (provided by inheriting class)
    if TYPE_CHECKING:
        hass: HomeAssistant

    def _get_subentries_by_type(self, entry_type: str) -> dict[str, dict[str, Any]]:
        """
        Get all sub-entries of a specific type.

        Handles legacy, new type names, and subentries in parent configs.
        """
        subentries = {}

        # Map legacy and new type names for global config
        entry_type_map = {
            "global": ["global_config"],  # Standardized to global_config only
            "group": ["group"],
            "window": ["window"],
            "group_configs": ["group_configs"],
            "window_configs": ["window_configs"],
        }
        valid_types = entry_type_map.get(entry_type, [entry_type])

        # Get all config entries for this domain
        domain_entries = self.hass.config_entries.async_entries("solar_window_system")

        for entry in domain_entries:
            # Direct match (classic style)
            if entry.data.get("entry_type") in valid_types:
                subentries[entry.entry_id] = entry.data

            # For window/group: also check subentries in parent configs
            if entry_type in ("window", "group") and hasattr(entry, "subentries"):
                for sub in entry.subentries.values():
                    if hasattr(sub, "data") and hasattr(sub, "subentry_type"):
                        sub_data = (
                            dict(sub.data) if hasattr(sub.data, "items") else sub.data
                        )
                        sub_type = getattr(sub, "subentry_type", None) or sub_data.get(
                            "entry_type"
                        )
                        sub_id = getattr(sub, "subentry_id", None) or getattr(
                            sub, "title", None
                        )
                    elif isinstance(sub, dict):
                        sub_data = sub.get("data", {})
                        sub_type = sub_data.get("entry_type") or sub.get(
                            "subentry_type"
                        )
                        sub_id = sub.get("subentry_id") or sub.get("title")
                    else:
                        continue  # skip unknown subentry type
                    if (
                        sub_type == entry_type
                        or sub_data.get("entry_type") == entry_type
                    ) and sub_id:
                        subentries[sub_id] = sub_data

        return subentries

    def get_effective_config_from_flows(
        self, window_subentry_id: str
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Get effective configuration using flow-based inheritance."""
        # Get all relevant subentries
        windows = self._get_subentries_by_type("window")
        groups = self._get_subentries_by_type("group")

        if window_subentry_id not in windows:
            msg = f"Window configuration not found: {window_subentry_id}"
            raise ValueError(msg)

        window_data = windows[window_subentry_id]

        # Start with global configuration (merged from data and options)
        global_config = self._get_global_data_merged()
        global_sources = {}
        if global_config:
            # Mark all values as coming from global
            global_sources = self._mark_config_sources(global_config, "global")

        # Apply group configuration if linked
        group_config = {}
        linked_group_id = window_data.get("linked_group_id")
        if linked_group_id and linked_group_id in groups:
            group_config = groups[linked_group_id]

        # Build effective configuration
        effective_config = self._build_effective_config(
            global_config, group_config, window_data
        )

        # Build source tracking
        effective_sources = self._build_effective_sources(global_sources, window_data)

        return effective_config, effective_sources

    def _mark_config_sources(
        self, config: dict[str, Any], source: str
    ) -> dict[str, Any]:
        """Mark all configuration values with their source."""
        sources = {}
        for key, value in config.items():
            if isinstance(value, dict):
                sources[key] = self._mark_config_sources(value, source)
            else:
                sources[key] = source
        return sources

    def _build_effective_config(
        self,
        global_config: dict[str, Any],
        group_config: dict[str, Any],
        window_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Build effective configuration with inheritance.

        Respecting explicit inheritance markers.
        """
        # Start with global as base
        effective = self._copy_config(global_config)

        # Override with group config, but skip inherit markers
        self._merge_config_layer(effective, group_config)

        # Override with window-specific data, but skip inherit markers
        self._merge_config_layer(effective, window_data)

        # Structure flat config into expected nested format for apply_global_factors
        return self._structure_flat_config(effective)

    def _copy_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Create a deep copy of configuration."""
        result = {}
        for key, value in config.items():
            if isinstance(value, dict):
                result[key] = value.copy()
            else:
                result[key] = value
        return result

    def _merge_config_layer(
        self, effective: dict[str, Any], layer_config: dict[str, Any]
    ) -> None:
        """Merge a configuration layer into the effective config."""

        def is_inherit_marker(val: Any) -> bool:
            return val in ("-1", -1, "", None, "inherit")

        for key, value in layer_config.items():
            if is_inherit_marker(value):
                continue

            if self._should_merge_nested(effective, key, value):
                self._merge_nested_dict(effective, key, value)
            else:
                effective[key] = value

    def _should_merge_nested(
        self, effective: dict[str, Any], key: str, value: Any
    ) -> bool:
        """Check if we should merge nested dictionaries."""
        return (
            key in effective
            and isinstance(effective[key], dict)
            and isinstance(value, dict)
        )

    def _merge_nested_dict(
        self, effective: dict[str, Any], key: str, value: dict[str, Any]
    ) -> None:
        """Merge nested dictionary values."""

        def is_inherit_marker(val: Any) -> bool:
            return val in ("-1", -1, "", None, "inherit")

        for subkey, subval in value.items():
            if not is_inherit_marker(subval):
                effective[key][subkey] = subval

    def _structure_flat_config(self, flat_config: dict[str, Any]) -> dict[str, Any]:
        """Structure flat config into nested format expected by apply_global_factors."""
        structured = {
            "thresholds": {
                "direct": flat_config.get("threshold_direct", 200),
                "diffuse": flat_config.get("threshold_diffuse", 150),
            },
            "temperatures": {
                "indoor_base": flat_config.get("temperature_indoor_base", 23.0),
                "outdoor_base": flat_config.get("temperature_outdoor_base", 19.5),
            },
            "physical": {
                "g_value": flat_config.get("g_value", 0.5),
                "frame_width": flat_config.get("frame_width", 0.125),
                "diffuse_factor": flat_config.get("diffuse_factor", 0.15),
                "tilt": flat_config.get("tilt", 90.0),
            },
            "shadow": {
                "depth": flat_config.get("shadow_depth", 0.0),
                "offset": flat_config.get("shadow_offset", 0.0),
            },
        }

        # Preserve any custom parameters that don't fit the predefined structure
        known_keys = {
            "threshold_direct",
            "threshold_diffuse",
            "temperature_indoor_base",
            "temperature_outdoor_base",
            "g_value",
            "frame_width",
            "diffuse_factor",
            "tilt",
            "shadow_depth",
            "shadow_offset",
        }

        # Add custom parameters using dictionary comprehension
        custom_params = {
            key: value for key, value in flat_config.items() if key not in known_keys
        }
        structured.update(custom_params)

        return structured

    def _build_effective_sources(
        self,
        global_sources: dict[str, Any],
        window_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Build effective sources tracking."""
        # Start with global sources
        sources = self._copy_config(global_sources)

        # Mark window data as window source
        window_sources = self._mark_config_sources(window_data, "window")
        for key, value in window_sources.items():
            if (
                key in sources
                and isinstance(sources[key], dict)
                and isinstance(value, dict)
            ):
                sources[key].update(value)
            else:
                sources[key] = value

        return sources

    def _get_global_data_merged(self) -> dict[str, Any]:
        """Get merged global data from global config entry and entities."""
        # Get global config data (merge data and options with options priority)
        global_data = {}
        global_configs = self._get_subentries_by_type("global")

        if global_configs:
            global_entry_id = next(iter(global_configs))
            global_data = global_configs[global_entry_id].copy()

            # Find config entry and merge options over data (options have priority)
            for entry in self.hass.config_entries.async_entries("solar_window_system"):
                entry_type = entry.data.get("entry_type")

                # Check for global_config only (standardized)
                if entry_type in ["global_config"]:
                    # Start with data as base
                    merged_config = dict(entry.data)

                    # Options override data (priority system)
                    if entry.options:
                        merged_config.update(entry.options)

                    # Now replace the global_data with merged config
                    global_data = merged_config
                    break

        return global_data

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

    def _extract_calculation_parameters(
        self,
        effective_config: dict[str, Any],
        window_data: dict[str, Any],
        states: dict[str, Any],
    ) -> tuple[float, float, float, float, float, float, float, float, float]:
        """Extract and validate calculation parameters."""
        solar_radiation = self._safe_float_conversion(
            states.get("solar_radiation", 0.0), 0.0
        )
        sun_azimuth = self._safe_float_conversion(states.get("sun_azimuth", 0.0), 0.0)
        sun_elevation = self._safe_float_conversion(
            states.get("sun_elevation", 0.0), 0.0
        )

        # Physical parameters
        g_value = self._safe_float_conversion(
            effective_config["physical"].get("g_value", 0.5), 0.5
        )
        frame_width = self._safe_float_conversion(
            effective_config["physical"].get("frame_width", 0.125), 0.125
        )
        diffuse_factor = self._safe_float_conversion(
            effective_config["physical"].get("diffuse_factor", 0.15), 0.15
        )
        tilt = self._safe_float_conversion(
            effective_config["physical"].get("tilt", 90.0), 90.0
        )

        # Window dimensions
        window_width = self._safe_float_conversion(
            window_data.get("window_width", 1.0), 1.0
        )
        window_height = self._safe_float_conversion(
            window_data.get("window_height", 1.0), 1.0
        )
        glass_width = max(0, window_width - 2 * frame_width)
        glass_height = max(0, window_height - 2 * frame_width)
        area = glass_width * glass_height

        # Shadow parameters - check effective_config first, then window_data
        shadow_depth = self._safe_float_conversion(
            effective_config.get("shadow_depth", window_data.get("shadow_depth", 0)),
            0.0,
        )
        shadow_offset = self._safe_float_conversion(
            effective_config.get("shadow_offset", window_data.get("shadow_offset", 0)),
            0.0,
        )

        return (
            solar_radiation,
            sun_azimuth,
            sun_elevation,
            g_value,
            diffuse_factor,
            tilt,
            area,
            shadow_depth,
            shadow_offset,
        )
