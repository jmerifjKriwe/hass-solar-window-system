"""Options flow for Solar Window System integration."""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from collections.abc import Mapping

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector

from .helpers import get_temperature_sensor_entities

_LOGGER = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

# Lint-friendly messages
MSG_BELOW_MIN = "value below minimum"
MSG_ABOVE_MAX = "value above maximum"


# Locale-aware parsing helpers (module-scoped to keep methods simpler)
def _normalize_decimal_string(v: Any) -> str:
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, str):
        return v.strip().replace(",", ".")
    return str(v)


def _parse_float_locale(v: Any) -> float:
    return float(_normalize_decimal_string(v))


def _parse_int_locale(v: Any) -> int:
    return int(float(_normalize_decimal_string(v)))


def allow_empty_float(min_v: float | None = None, max_v: float | None = None) -> Any:
    """Return validator that allows empty values and coerces floats with bounds."""

    def _validator(v: Any) -> Any:
        if v in ("", None, "-1", -1):
            return ""
        fv = _parse_float_locale(v)
        if min_v is not None and fv < min_v:
            msg = MSG_BELOW_MIN
            raise vol.Invalid(msg)
        if max_v is not None and fv > max_v:
            msg = MSG_ABOVE_MAX
            raise vol.Invalid(msg)
        return fv

    return _validator


def allow_empty_int(min_v: int | None = None, max_v: int | None = None) -> Any:
    """Return validator that allows empty values and coerces ints with bounds."""

    def _validator(v: Any) -> Any:
        if v in ("", None, "-1", -1):
            return ""
        iv = _parse_int_locale(v)
        if min_v is not None and iv < min_v:
            msg = MSG_BELOW_MIN
            raise vol.Invalid(msg)
        if max_v is not None and iv > max_v:
            msg = MSG_ABOVE_MAX
            raise vol.Invalid(msg)
        return iv

    return _validator


# Keys used across flows
_FIELDS_FLOAT = (
    "diffuse_factor",
    "temperature_indoor_base",
    "temperature_outdoor_base",
)
_FIELDS_INT = (
    "threshold_direct",
    "threshold_diffuse",
)
_WINDOW_OVERRIDE_FLOAT = (
    "g_value",
    "frame_width",
    "tilt",
    "diffuse_factor",
    "temperature_indoor_base",
    "temperature_outdoor_base",
)
_WINDOW_OVERRIDE_INT = (
    "threshold_direct",
    "threshold_diffuse",
)


class SolarWindowSystemOptionsFlow(config_entries.OptionsFlow):
    """
    Options flow for Solar Window System integration.

    Handles window and group options flows, including required and optional selectors.
    """

    # ----- Group options flow (per group) -----
    async def async_step_group_options(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Options flow for a single group with inheritance from Global when empty."""
        _LOGGER.error(
            "DEBUG: async_step_group_options STARTED, user_input=%r", user_input
        )

        opts = self.config_entry.options or {}
        data = self.config_entry.data or {}

        _LOGGER.error("DEBUG: GROUP OPTIONS - opts=%r", opts)
        _LOGGER.error("DEBUG: GROUP OPTIONS - data=%r", data)

        global_data = self._get_global_data()
        temp_sensor_options = await get_temperature_sensor_entities(self.hass)

        schema = self._build_group_options_schema(
            temp_sensor_options, opts, data, global_data
        )

        if user_input is None:
            _LOGGER.error("DEBUG: GROUP OPTIONS - showing form (first load)")
            return self.async_show_form(step_id="group_options", data_schema=schema)

        _LOGGER.error("DEBUG: GROUP OPTIONS - processing user_input=%r", user_input)

        # Validate input manually to handle type conversion errors gracefully
        errors: dict[str, str] = {}
        validated_result = self._validate_group_input(user_input, errors)

        if errors:
            # Re-create schema with user input as defaults for error display
            error_schema = self._build_group_options_schema_with_user_input(
                temp_sensor_options, user_input
            )
            return self.async_show_form(
                step_id="group_options", data_schema=error_schema, errors=errors
            )

        # Only keep non-empty values for storage
        result = self._build_group_result(validated_result)
        return self.async_create_entry(title=result.get("name", ""), data=result)

    def _get_global_data(self) -> dict[str, Any]:
        """Return global configuration entry data if available."""
        for entry in self.hass.config_entries.async_entries(self.config_entry.domain):
            if entry.data.get("entry_type") == "global_config":
                # Merge options over data (options are the current global values)
                merged: dict[str, Any] = dict(entry.data)
                # Defensive: options may be a mapping proxy; ignore if not mutable
                with contextlib.suppress(Exception):
                    merged.update(entry.options or {})
                return merged
        return {}

    @staticmethod
    def _prefer_options(
        opts: Mapping[str, Any],
        data: Mapping[str, Any],
        key: str,
        fallback: Any = "",
    ) -> Any:
        """Prefer an explicit value in options, else fallback to data."""
        if key in opts:
            return opts.get(key, fallback)
        return data.get(key, fallback)

    def _build_group_options_schema(
        self,
        temp_sensor_options: list[dict],
        opts: Mapping[str, Any],
        data: Mapping[str, Any],
        _global_data: dict[str, Any],
    ) -> vol.Schema:
        """Construct the schema for group options with inheritance suggestions."""
        schema_dict: dict[Any, Any] = {}
        name_default = str(self._prefer_options(opts, data, "name", ""))
        schema_dict[vol.Required("name", default=name_default)] = str

        # Use new key name for group/window local sensor that may override global
        room_default = self._prefer_options(opts, data, "indoor_temperature_sensor", "")
        room_default_str = "" if room_default in ("", None) else str(room_default)
        schema_dict[
            vol.Required(
                "indoor_temperature_sensor",
                description={
                    "suggested_value": room_default_str,
                    "translation_key": "indoor_temperature_sensor",
                },
            )
        ] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=cast("Any", temp_sensor_options),
                custom_value=True,
            )
        )

        # For numeric overrides: always coerce to string for default
        for key in (*_FIELDS_FLOAT, *_FIELDS_INT):
            cur_val = self._prefer_options(opts, data, key, "")
            _LOGGER.error(
                "DEBUG GROUP BUILD SCHEMA: key=%s, cur_val=%r (type=%s)",
                key,
                cur_val,
                type(cur_val),
            )
            default_val = "" if cur_val in (None, "") else str(cur_val)
            _LOGGER.error(
                "DEBUG GROUP BUILD SCHEMA: key=%s, default_val=%r (type=%s)",
                key,
                default_val,
                type(default_val),
            )
            try:
                schema_dict[vol.Optional(key, default=default_val)] = str
                _LOGGER.error(
                    "DEBUG GROUP BUILD SCHEMA: key=%s, schema creation SUCCESS", key
                )
            except Exception as e:
                _LOGGER.error(
                    "DEBUG GROUP BUILD SCHEMA: key=%s, schema creation FAILED: %s",
                    key,
                    e,
                )
                raise

        return vol.Schema(schema_dict)

    def _build_group_options_schema_with_user_input(
        self,
        temp_sensor_options: list[dict],
        user_input: dict[str, Any],
    ) -> vol.Schema:
        """Build group options schema with user input as defaults for error display."""
        schema_dict: dict[Any, Any] = {}

        # Name field with user input as default
        name_default = str(user_input.get("name", ""))
        schema_dict[vol.Required("name", default=name_default)] = str

        # Indoor temperature sensor with user input as default
        sensor_default = str(user_input.get("indoor_temperature_sensor", ""))
        schema_dict[
            vol.Required(
                "indoor_temperature_sensor",
                default=sensor_default,
                description={
                    "suggested_value": sensor_default,
                    "translation_key": "indoor_temperature_sensor",
                },
            )
        ] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=cast("Any", temp_sensor_options),
                custom_value=True,
            )
        )

        # Numeric fields with user input as defaults
        for key in (*_FIELDS_FLOAT, *_FIELDS_INT):
            user_val = user_input.get(key, "")
            default_val = str(user_val) if user_val not in (None, "") else ""
            schema_dict[vol.Optional(key, default=default_val)] = str

        return vol.Schema(schema_dict)

    def _validate_group_input(
        self, user_input: dict[str, Any], errors: dict[str, str]
    ) -> dict[str, Any]:
        """Validate group options input and populate errors dict."""
        validated_result: dict[str, Any] = {}

        # Validate name (required string)
        name = user_input.get("name", "").strip()
        if not name:
            errors["name"] = "required"
        else:
            validated_result["name"] = name

        # Validate indoor temperature sensor (required)
        sensor = user_input.get("indoor_temperature_sensor", "")
        if sensor in (None, ""):
            errors["indoor_temperature_sensor"] = "required"
        else:
            validated_result["indoor_temperature_sensor"] = (
                "" if sensor in ("-1", -1) else sensor
            )

        # Validate numeric fields with locale-aware parsing
        def _validate_float_field(field: str, min_v: float, max_v: float) -> None:
            raw = user_input.get(field, "")
            if raw in (None, "", "-1"):
                # Allow empty for inheritance
                validated_result[field] = ""
                return
            try:
                fv = self._parse_float_locale(raw)
                if fv < min_v or fv > max_v:
                    errors[field] = "number_out_of_range"
                else:
                    validated_result[field] = str(raw)
            except (ValueError, TypeError):
                errors[field] = "invalid_number"

        def _validate_int_field(field: str, min_v: int, max_v: int) -> None:
            raw = user_input.get(field, "")
            if raw in (None, "", "-1"):
                # Allow empty for inheritance
                validated_result[field] = ""
                return
            try:
                iv = self._parse_int_locale(raw)
                if iv < min_v or iv > max_v:
                    errors[field] = "number_out_of_range"
                else:
                    validated_result[field] = str(raw)
            except (ValueError, TypeError):
                errors[field] = "invalid_number"

        # Validate all numeric fields
        _validate_float_field("diffuse_factor", 0.05, 0.5)
        _validate_int_field("threshold_direct", 0, 1000)
        _validate_int_field("threshold_diffuse", 0, 1000)
        _validate_float_field("temperature_indoor_base", 10, 30)
        _validate_float_field("temperature_outdoor_base", 10, 30)

        return validated_result

    @staticmethod
    def _build_group_result(validated_result: dict[str, Any]) -> dict[str, Any]:
        """Build the final result dict for group options."""
        result = {"name": validated_result["name"]}
        if validated_result.get("indoor_temperature_sensor"):
            result["indoor_temperature_sensor"] = validated_result[
                "indoor_temperature_sensor"
            ]

        for field in (
            "diffuse_factor",
            "threshold_direct",
            "threshold_diffuse",
            "temperature_indoor_base",
            "temperature_outdoor_base",
        ):
            if validated_result.get(field):
                result[field] = validated_result[field]

        return result

    @staticmethod
    def _parse_group_options_result(user_input: dict[str, Any]) -> dict[str, Any]:
        """Coerce group options inputs while keeping empties for inheritance."""
        result: dict[str, Any] = {
            "name": user_input.get("name", ""),
            "indoor_temperature_sensor": ""
            if user_input.get("indoor_temperature_sensor") in ("-1", -1)
            else user_input.get("indoor_temperature_sensor", ""),
        }
        # For required numeric fields, do not allow empty or inherit marker
        for k in (
            "diffuse_factor",
            "threshold_direct",
            "threshold_diffuse",
            "temperature_indoor_base",
            "temperature_outdoor_base",
        ):
            val = user_input.get(k, "")
            if val not in (None, "", "-1"):
                result[k] = str(val)
        return result

    # ----- Window options flow (per window) -----
    async def async_step_window_options(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Options for a window: manage linked group and overrides with inheritance."""
        _LOGGER.error(
            "DEBUG: async_step_window_options STARTED, user_input=%r", user_input
        )

        opts = self.config_entry.options or {}
        data = self.config_entry.data or {}

        _LOGGER.error("DEBUG: WINDOW OPTIONS - opts=%r", opts)
        _LOGGER.error("DEBUG: WINDOW OPTIONS - data=%r", data)

        group_options_map = self._get_group_options_map()
        global_data = self._get_global_data()

        linked_group_id = self._prefer_options(opts, data, "linked_group_id", "")
        linked_group_name = self._resolve_group_name(linked_group_id, group_options_map)
        if not linked_group_name:
            linked_group_name = self._prefer_options(opts, data, "linked_group", "")

        ctx = self._WindowCtx(
            group_options_map=group_options_map,
            linked_group_id=linked_group_id,
            linked_group_name=linked_group_name,
            global_data=global_data,
        )
        temp_sensor_options = await get_temperature_sensor_entities(self.hass)

        schema = self._build_window_options_schema(
            opts,
            data,
            ctx,
            temp_sensor_options,
        )

        if user_input is None:
            return self.async_show_form(step_id="window_options", data_schema=schema)

        result = self._parse_window_options_result(user_input, group_options_map)
        return self.async_create_entry(title=result.get("name", ""), data=result)

    def _get_group_options_map(self) -> list[tuple[str, str]]:
        """Return list of (group_id, group_title)."""
        result: list[tuple[str, str]] = []
        for entry in self.hass.config_entries.async_entries(self.config_entry.domain):
            if entry.data.get("entry_type") == "group_configs" and entry.subentries:
                for sub_id, sub in entry.subentries.items():
                    # Be permissive: tests provide MockConfigEntry without subentry_type
                    sub_type = getattr(sub, "subentry_type", "group")
                    if sub_type == "group":
                        result.append((sub_id, sub.title or f"Group {sub_id}"))
        return result

    @staticmethod
    def _resolve_group_name(
        group_id: str, group_options_map: list[tuple[str, str]]
    ) -> str:
        if not group_id:
            return ""
        for gid, gname in group_options_map:
            if gid == group_id:
                return gname
        return ""

    def _inherit_from_group_or_global(
        self,
        key: str,
        linked_group_id: str,
        global_data: dict[str, Any],
    ) -> Any:
        # Try group subentry first
        if linked_group_id:
            for entry in self.hass.config_entries.async_entries(
                self.config_entry.domain
            ):
                if entry.data.get("entry_type") == "group_configs" and getattr(
                    entry, "subentries", None
                ):
                    sub = entry.subentries.get(linked_group_id)
                    if sub and sub.data.get(key) not in ("", None):
                        return sub.data.get(key)
                    break
        # Fallback to global
        return global_data.get(key, "")

    @dataclass
    class _WindowCtx:
        group_options_map: list[tuple[str, str]]
        linked_group_id: str
        linked_group_name: str
        global_data: dict[str, Any]

    def _build_window_options_schema(
        self,
        opts: Mapping[str, Any],
        data: Mapping[str, Any],
        ctx: _WindowCtx,
        temp_sensor_options: list[dict],
    ) -> vol.Schema:
        schema_dict: dict[Any, Any] = {}
        name_def = str(self._prefer_options(opts, data, "name", ""))
        schema_dict[vol.Required("name", default=name_def)] = str

        # indoor temp sensor: suggest current value only (use shared async helper)
        # Note: helper returns list[SelectOptionDict]-like dicts with value/label
        rte_def = self._prefer_options(opts, data, "indoor_temperature_sensor", "")
        rte_def_str = "" if rte_def in ("", None) else str(rte_def)
        schema_dict[
            vol.Optional(
                "indoor_temperature_sensor",
                description={"suggested_value": rte_def_str},
            )
        ] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=cast("Any", temp_sensor_options),
                custom_value=True,
            )
        )

        if ctx.group_options_map:
            show_name = ctx.linked_group_name or ""
            schema_dict[
                vol.Optional("linked_group", description={"suggested_value": show_name})
            ] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[name for _, name in ctx.group_options_map],
                    custom_value=True,
                )
            )

        # overrides: suggest from group or global only if current value is empty
        for key in (*_WINDOW_OVERRIDE_FLOAT, *_WINDOW_OVERRIDE_INT):
            cur_val = self._prefer_options(opts, data, key, "")
            if cur_val in ("", None):
                suggested = self._inherit_from_group_or_global(
                    key, ctx.linked_group_id, ctx.global_data
                )
            else:
                suggested = cur_val

            # Convert suggested value to string for display
            suggested_str = "" if suggested in ("", None) else str(suggested)

            _LOGGER.error(
                "DEBUG WINDOW BUILD SCHEMA: key=%s, cur_val=%r (type=%s), suggested=%r (type=%s), suggested_str=%r (type=%s)",
                key,
                cur_val,
                type(cur_val),
                suggested,
                type(suggested),
                suggested_str,
                type(suggested_str),
            )

            # Attach description on value (read via schema[key].description)
            try:
                schema_dict[
                    vol.Optional(key, description={"suggested_value": suggested_str})
                ] = str
                _LOGGER.error(
                    "DEBUG WINDOW BUILD SCHEMA: key=%s, schema creation SUCCESS", key
                )
            except Exception as e:
                _LOGGER.error(
                    "DEBUG WINDOW BUILD SCHEMA: key=%s, schema creation FAILED: %s",
                    key,
                    e,
                )
                raise

        return vol.Schema(schema_dict)

    @staticmethod
    def _parse_window_options_result(
        user_input: dict[str, Any],
        group_options_map: list[tuple[str, str]],
    ) -> dict[str, Any]:
        result: dict[str, Any] = {"name": user_input.get("name", "")}
        # Store under new key name but keep compatibility: accept old key
        raw_sensor = user_input.get("room_temp_entity", "") or user_input.get(
            "indoor_temperature_sensor", ""
        )
        result["indoor_temperature_sensor"] = (
            "" if raw_sensor in ("-1", -1) else raw_sensor
        )

        # Resolve linked group name to id
        sel_group_name = user_input.get("linked_group", "")
        sel_group_id = ""
        if sel_group_name:
            for gid, gname in group_options_map:
                if gname == sel_group_name:
                    sel_group_id = gid
                    break
        result["linked_group"] = sel_group_name or ""
        result["linked_group_id"] = sel_group_id

        # Coerce overrides
        for k in _WINDOW_OVERRIDE_FLOAT:
            if k in user_input:
                result[k] = allow_empty_float()(user_input.get(k))
        for k in _WINDOW_OVERRIDE_INT:
            if k in user_input:
                result[k] = allow_empty_int()(user_input.get(k))
        return result

    """Handle options flow for Solar Window System."""

    """Handle options flow for Solar Window System."""

    def __init__(self, _config_entry: config_entries.ConfigEntry) -> None:
        """Initialize the options flow."""
        # Do not assign to self.config_entry; Home Assistant sets it.
        # Keep accepting the parameter for compatibility if needed by future logic.
        # page storages
        self._p1: dict[str, Any] | None = None
        self._p2: dict[str, Any] | None = None

    @staticmethod
    def _get_temperature_sensor_entities(hass: Any) -> list[str]:
        """Collect temperature sensor entity_ids to present as options."""
        entity_registry = er.async_get(hass)
        temperature_entities: list[str] = []
        for ent in entity_registry.entities.values():
            if (
                ent.entity_id.startswith("sensor.")
                and not ent.disabled_by
                and not ent.hidden_by
            ):
                state = hass.states.get(ent.entity_id)
                if state and state.attributes.get("unit_of_measurement") in (
                    "°C",
                    "°F",
                    "K",
                ):
                    temperature_entities.append(ent.entity_id)
        return temperature_entities

    @staticmethod
    def _get_warning_source_entities(hass: Any) -> list[str]:
        """Collect binary_sensor and input_boolean entity_ids to present as options."""
        entity_registry = er.async_get(hass)
        sources: list[str] = [
            ent.entity_id
            for ent in entity_registry.entities.values()
            if (
                (
                    ent.entity_id.startswith("binary_sensor.")
                    or ent.entity_id.startswith("input_boolean.")
                )
                and not ent.disabled_by
                and not ent.hidden_by
            )
        ]
        return sources

    # ----- Locale-aware parsing helpers -----
    @staticmethod
    def _normalize_decimal_string(v: Any) -> str:
        """
        Normalize decimal separator for parsing.

        Accept strings with comma as decimal separator by converting to dot.
        Also handle numeric inputs by converting to string.
        """
        if isinstance(v, (int, float)):
            return str(v)
        if isinstance(v, str):
            return v.strip().replace(",", ".")
        return str(v)

    @classmethod
    def _parse_float_locale(cls, v: Any) -> float:
        return float(cls._normalize_decimal_string(v))

    @classmethod
    def _parse_int_locale(cls, v: Any) -> int:
        return int(float(cls._normalize_decimal_string(v)))

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Start options flow, routing by entry type."""
        entry_type = (self.config_entry.data or {}).get("entry_type", "")
        if entry_type == "group":
            return await self.async_step_group_options(user_input)
        if entry_type == "window":
            return await self.async_step_window_options(user_input)
        # Default: Global Configuration options
        return await self.async_step_global_basic(user_input)

    # ----- Page 1: Basic geometry + optional selectors -----
    async def async_step_global_basic(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Options page 1: basic geometry and optional selectors."""
        opts = self.config_entry.options or {}
        data = self.config_entry.data or {}

        # build defaults from options with fallback to data
        def _g(key: str, fallback: Any = "") -> Any:
            return opts.get(key, data.get(key, fallback))

        def _sel_default(v: Any) -> Any:
            # For entity selector, None or "" renders as empty/cleared in UI
            return v if v else None

        def _sel_default_with_fallback(key: str) -> Any:
            # If key explizit in options, respektiere ihn (auch "")
            if key in opts:
                return _sel_default(opts.get(key))
            # Sonst fallback auf data
            return _sel_default(data.get(key, ""))

        defaults = {
            "window_width": str(_g("window_width", "")),
            "window_height": str(_g("window_height", "")),
            "shadow_depth": str(_g("shadow_depth", "")),
            "shadow_offset": str(_g("shadow_offset", "")),
            "solar_radiation_sensor": _sel_default_with_fallback(
                "solar_radiation_sensor"
            ),
            "outdoor_temperature_sensor": _sel_default_with_fallback(
                "outdoor_temperature_sensor"
            ),
            "indoor_temperature_sensor": _sel_default_with_fallback(
                "indoor_temperature_sensor"
            ),
            # For selectors: use options if present, else fallback to data
            "forecast_temperature_sensor": _sel_default_with_fallback(
                "forecast_temperature_sensor"
            ),
            "weather_warning_sensor": _sel_default_with_fallback(
                "weather_warning_sensor"
            ),
        }

        # Prefer entity selectors over static lists for a true dropdown widget
        if user_input is None:
            schema = vol.Schema(
                {
                    vol.Required("window_width", default=defaults["window_width"]): str,
                    vol.Required(
                        "window_height", default=defaults["window_height"]
                    ): str,
                    vol.Required("shadow_depth", default=defaults["shadow_depth"]): str,
                    vol.Required(
                        "shadow_offset", default=defaults["shadow_offset"]
                    ): str,
                    vol.Required(
                        "solar_radiation_sensor",
                        description={
                            "suggested_value": defaults["solar_radiation_sensor"]
                        },
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain=["sensor"])
                    ),
                    vol.Required(
                        "outdoor_temperature_sensor",
                        description={
                            "suggested_value": defaults["outdoor_temperature_sensor"]
                        },
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=["sensor"], device_class="temperature"
                        )
                    ),
                    vol.Optional(
                        "indoor_temperature_sensor",
                        description={
                            "suggested_value": defaults["indoor_temperature_sensor"]
                        },
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=["sensor"], device_class="temperature"
                        )
                    ),
                    vol.Optional(
                        "forecast_temperature_sensor",
                        description={
                            "suggested_value": defaults["forecast_temperature_sensor"]
                        },
                    ): vol.Any(
                        None,
                        selector.EntitySelector(
                            selector.EntitySelectorConfig(
                                domain=["sensor"], device_class="temperature"
                            )
                        ),
                    ),
                    vol.Optional(
                        "weather_warning_sensor",
                        description={
                            "suggested_value": defaults["weather_warning_sensor"]
                        },
                    ): vol.Any(
                        None,
                        selector.EntitySelector(
                            selector.EntitySelectorConfig(
                                domain=["binary_sensor", "input_boolean"]
                            )
                        ),
                    ),
                }
            )
            return self.async_show_form(step_id="global_basic", data_schema=schema)

        errors: dict[str, str] = {}
        page1: dict[str, Any] = {}

        def _check_float_required(field: str, min_v: float, max_v: float) -> None:
            raw = user_input.get(field)
            if raw in (None, "", "-1"):
                errors[field] = "required"
                return
            try:
                fv = self._parse_float_locale(raw)
            except (ValueError, TypeError):
                errors[field] = "invalid_number"
                return
            if fv < min_v or fv > max_v:
                errors[field] = "number_out_of_range"
                return
            page1[field] = str(raw)

        _check_float_required("window_width", 0.1, 10)
        _check_float_required("window_height", 0.1, 10)
        _check_float_required("shadow_depth", 0, 5)
        _check_float_required("shadow_offset", 0, 5)

        # Required selectors: indoor is also required
        for req_key in (
            "solar_radiation_sensor",
            "outdoor_temperature_sensor",
            "indoor_temperature_sensor",
        ):
            val = user_input.get(req_key)
            if val in (None, ""):
                errors[req_key] = "required"
            else:
                page1[req_key] = val

        # Optional selectors: allow clearing
        for key in ("forecast_temperature_sensor", "weather_warning_sensor"):
            val = user_input.get(key, "")
            page1[key] = "" if val in (None, "") else val

        if errors:
            schema = vol.Schema(
                {
                    vol.Required(
                        "window_width",
                        default=str(user_input.get("window_width", "")),
                    ): str,
                    vol.Required(
                        "window_height",
                        default=str(user_input.get("window_height", "")),
                    ): str,
                    vol.Required(
                        "shadow_depth",
                        default=str(user_input.get("shadow_depth", "")),
                    ): str,
                    vol.Required(
                        "shadow_offset",
                        default=str(user_input.get("shadow_offset", "")),
                    ): str,
                    vol.Required(
                        "solar_radiation_sensor",
                        default=_sel_default(
                            user_input.get("solar_radiation_sensor", "")
                        ),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain=["sensor"])
                    ),
                    vol.Required(
                        "outdoor_temperature_sensor",
                        default=_sel_default(
                            user_input.get("outdoor_temperature_sensor", "")
                        ),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=["sensor"], device_class="temperature"
                        )
                    ),
                    vol.Required(
                        "indoor_temperature_sensor",
                        default=_sel_default(
                            user_input.get("indoor_temperature_sensor", "")
                        ),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=["sensor"], device_class="temperature"
                        )
                    ),
                    vol.Optional(
                        "forecast_temperature_sensor",
                        default=_sel_default(
                            user_input.get("forecast_temperature_sensor", "")
                        ),
                    ): vol.Any(
                        None,
                        selector.EntitySelector(
                            selector.EntitySelectorConfig(
                                domain=["sensor"], device_class="temperature"
                            )
                        ),
                    ),
                    vol.Optional(
                        "weather_warning_sensor",
                        default=_sel_default(
                            user_input.get("weather_warning_sensor", "")
                        ),
                    ): vol.Any(
                        None,
                        selector.EntitySelector(
                            selector.EntitySelectorConfig(
                                domain=["binary_sensor", "input_boolean"]
                            )
                        ),
                    ),
                }
            )
            return self.async_show_form(
                step_id="global_basic",
                data_schema=schema,
                errors=errors,
            )

        self._p1 = page1

        return await self.async_step_global_enhanced()

    # ----- Page 2: Required defaults -----
    async def async_step_global_enhanced(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Options page 2: required global defaults (validated)."""
        opts = self.config_entry.options or {}
        data = self.config_entry.data or {}

        def _g(key: str, fallback: Any = "") -> Any:
            return opts.get(key, data.get(key, fallback))

        defaults = {
            "g_value": str(_g("g_value", 0.5)),
            "frame_width": str(_g("frame_width", 0.125)),
            "tilt": str(_g("tilt", 90)),
            "diffuse_factor": str(_g("diffuse_factor", 0.15)),
            "threshold_direct": str(_g("threshold_direct", 200)),
            "threshold_diffuse": str(_g("threshold_diffuse", 150)),
            "temperature_indoor_base": str(_g("temperature_indoor_base", 23.0)),
            "temperature_outdoor_base": str(_g("temperature_outdoor_base", 19.5)),
        }

        if user_input is None:
            schema = vol.Schema(
                {
                    vol.Required("g_value", default=defaults["g_value"]): str,
                    vol.Required("frame_width", default=defaults["frame_width"]): str,
                    vol.Required("tilt", default=defaults["tilt"]): str,
                    vol.Required(
                        "diffuse_factor", default=defaults["diffuse_factor"]
                    ): str,
                    vol.Required(
                        "threshold_direct", default=defaults["threshold_direct"]
                    ): str,
                    vol.Required(
                        "threshold_diffuse", default=defaults["threshold_diffuse"]
                    ): str,
                    vol.Required(
                        "temperature_indoor_base",
                        default=defaults["temperature_indoor_base"],
                    ): str,
                    vol.Required(
                        "temperature_outdoor_base",
                        default=defaults["temperature_outdoor_base"],
                    ): str,
                }
            )
            return self.async_show_form(step_id="global_enhanced", data_schema=schema)

        # per-field validation with locale-aware parsing
        errors2: dict[str, str] = {}
        page2: dict[str, Any] = {}

        def _check_float_required(field: str, min_v: float, max_v: float) -> None:
            raw = user_input.get(field)
            if raw in (None, "", "-1"):
                errors2[field] = "required"
                return
            try:
                fv = self._parse_float_locale(raw)
            except (ValueError, TypeError):
                errors2[field] = "invalid_number"
                return
            if fv < min_v or fv > max_v:
                errors2[field] = "number_out_of_range"
                return
            page2[field] = str(raw)

        def _check_int_required(field: str, min_v: int, max_v: int) -> None:
            raw = user_input.get(field)
            if raw in (None, "", "-1"):
                errors2[field] = "required"
                return
            try:
                iv = self._parse_int_locale(raw)
            except (ValueError, TypeError):
                errors2[field] = "invalid_number"
                return
            if iv < min_v or iv > max_v:
                errors2[field] = "number_out_of_range"
                return
            page2[field] = str(raw)

        _check_float_required("g_value", 0.1, 0.9)
        _check_float_required("frame_width", 0.05, 0.3)
        _check_int_required("tilt", 0, 90)
        _check_float_required("diffuse_factor", 0.05, 0.5)
        _check_int_required("threshold_direct", 0, 1000)
        _check_int_required("threshold_diffuse", 0, 1000)
        _check_float_required("temperature_indoor_base", 10, 30)
        _check_float_required("temperature_outdoor_base", 10, 30)

        if errors2:
            schema = vol.Schema(
                {
                    vol.Required(
                        "g_value", default=str(user_input.get("g_value", ""))
                    ): str,
                    vol.Required(
                        "frame_width", default=str(user_input.get("frame_width", ""))
                    ): str,
                    vol.Required("tilt", default=str(user_input.get("tilt", ""))): str,
                    vol.Required(
                        "diffuse_factor",
                        default=str(user_input.get("diffuse_factor", "")),
                    ): str,
                    vol.Required(
                        "threshold_direct",
                        default=str(user_input.get("threshold_direct", "")),
                    ): str,
                    vol.Required(
                        "threshold_diffuse",
                        default=str(user_input.get("threshold_diffuse", "")),
                    ): str,
                    vol.Required(
                        "temperature_indoor_base",
                        default=str(user_input.get("temperature_indoor_base", "")),
                    ): str,
                    vol.Required(
                        "temperature_outdoor_base",
                        default=str(user_input.get("temperature_outdoor_base", "")),
                    ): str,
                }
            )
            return self.async_show_form(
                step_id="global_enhanced",
                data_schema=schema,
                errors=errors2,
            )

        self._p2 = page2

        return await self.async_step_global_scenarios()

    # ----- Page 3: Scenario thresholds -----
    async def async_step_global_scenarios(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Options page 3: scenario thresholds (validated)."""
        opts = self.config_entry.options or {}
        data = self.config_entry.data or {}

        def _g(key: str, fallback: Any = "") -> Any:
            return opts.get(key, data.get(key, fallback))

        defaults = {
            "scenario_b_temp_indoor": str(_g("scenario_b_temp_indoor", 23.5)),
            "scenario_b_temp_outdoor": str(_g("scenario_b_temp_outdoor", 25.5)),
            "scenario_c_temp_indoor": str(_g("scenario_c_temp_indoor", 21.5)),
            "scenario_c_temp_outdoor": str(_g("scenario_c_temp_outdoor", 24.0)),
            "scenario_c_temp_forecast": str(_g("scenario_c_temp_forecast", 28.5)),
            "scenario_c_start_hour": str(_g("scenario_c_start_hour", 9)),
        }

        if user_input is None:
            schema = vol.Schema(
                {
                    vol.Required(
                        "scenario_b_temp_indoor",
                        default=defaults["scenario_b_temp_indoor"],
                    ): str,
                    vol.Required(
                        "scenario_b_temp_outdoor",
                        default=defaults["scenario_b_temp_outdoor"],
                    ): str,
                    vol.Required(
                        "scenario_c_temp_indoor",
                        default=defaults["scenario_c_temp_indoor"],
                    ): str,
                    vol.Required(
                        "scenario_c_temp_outdoor",
                        default=defaults["scenario_c_temp_outdoor"],
                    ): str,
                    vol.Required(
                        "scenario_c_temp_forecast",
                        default=defaults["scenario_c_temp_forecast"],
                    ): str,
                    vol.Required(
                        "scenario_c_start_hour",
                        default=defaults["scenario_c_start_hour"],
                    ): str,
                }
            )
            return self.async_show_form(step_id="global_scenarios", data_schema=schema)

        # validate page 3 with per-field errors and locale-aware parsing
        errors3: dict[str, str] = {}
        p3: dict[str, Any] = {}

        def _check_float_required(field: str, min_v: float, max_v: float) -> None:
            raw = user_input.get(field)
            if raw in (None, "", "-1"):
                errors3[field] = "required"
                return
            try:
                fv = self._parse_float_locale(raw)
            except (ValueError, TypeError):
                errors3[field] = "invalid_number"
                return
            if fv < min_v or fv > max_v:
                errors3[field] = "number_out_of_range"
                return
            p3[field] = str(raw)

        def _check_int_required(field: str, min_v: int, max_v: int) -> None:
            raw = user_input.get(field)
            if raw in (None, "", "-1"):
                errors3[field] = "required"
                return
            try:
                iv = self._parse_int_locale(raw)
            except (ValueError, TypeError):
                errors3[field] = "invalid_number"
                return
            if iv < min_v or iv > max_v:
                errors3[field] = "number_out_of_range"
                return
            p3[field] = str(raw)

        _check_float_required("scenario_b_temp_indoor", 10, 30)
        _check_float_required("scenario_b_temp_outdoor", 10, 30)
        _check_float_required("scenario_c_temp_indoor", 10, 30)
        _check_float_required("scenario_c_temp_outdoor", 10, 30)
        _check_float_required("scenario_c_temp_forecast", 15, 40)
        _check_int_required("scenario_c_start_hour", 0, 23)

        if errors3:
            schema = vol.Schema(
                {
                    vol.Required(
                        "scenario_b_temp_indoor",
                        default=str(user_input.get("scenario_b_temp_indoor", "")),
                    ): str,
                    vol.Required(
                        "scenario_b_temp_outdoor",
                        default=str(user_input.get("scenario_b_temp_outdoor", "")),
                    ): str,
                    vol.Required(
                        "scenario_c_temp_indoor",
                        default=str(user_input.get("scenario_c_temp_indoor", "")),
                    ): str,
                    vol.Required(
                        "scenario_c_temp_outdoor",
                        default=str(user_input.get("scenario_c_temp_outdoor", "")),
                    ): str,
                    vol.Required(
                        "scenario_c_temp_forecast",
                        default=str(user_input.get("scenario_c_temp_forecast", "")),
                    ): str,
                    vol.Required(
                        "scenario_c_start_hour",
                        default=str(user_input.get("scenario_c_start_hour", "")),
                    ): str,
                }
            )
            return self.async_show_form(
                step_id="global_scenarios",
                data_schema=schema,
                errors=errors3,
            )

        # Merge and save all pages
        data_out = {
            **(self._p1 or {}),
            **(self._p2 or {}),
            **p3,
        }
        return self.async_create_entry(title="", data=data_out)
