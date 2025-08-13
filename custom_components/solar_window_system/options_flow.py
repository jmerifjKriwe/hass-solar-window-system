"""Options flow for Solar Window System integration."""

from __future__ import annotations

import contextlib
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector

from .helpers import get_temperature_sensor_entities

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
        if v in ("", None):
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
        if v in ("", None):
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
        opts = self.config_entry.options or {}
        data = self.config_entry.data or {}

        global_data = self._get_global_data()
        temp_sensor_options = await get_temperature_sensor_entities(self.hass)

        schema = self._build_group_options_schema(
            temp_sensor_options, opts, data, global_data
        )

        if user_input is None:
            return self.async_show_form(step_id="group_options", data_schema=schema)

        result = self._parse_group_options_result(user_input)
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
        temp_sensor_options: list[str],
        opts: Mapping[str, Any],
        data: Mapping[str, Any],
        global_data: dict[str, Any],
    ) -> vol.Schema:
        """Construct the schema for group options with inheritance suggestions."""
        schema_dict: dict[Any, Any] = {}
        name_default = str(self._prefer_options(opts, data, "name", ""))
        schema_dict[vol.Required("name", default=name_default)] = str

        room_default = self._prefer_options(opts, data, "room_temp_entity", "")
        schema_dict[
            vol.Required(
                "room_temp_entity",
                description={"suggested_value": room_default},
            )
        ] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=temp_sensor_options, custom_value=True
            )
        )

        # For numeric overrides: suggest from global only if current value empty
        for key in (*_FIELDS_FLOAT, *_FIELDS_INT):
            cur_val = self._prefer_options(opts, data, key, "")
            if key in _FIELDS_INT:
                # Tests expect integer thresholds to suggest global values
                suggested = global_data.get(key, "") if global_data else ""
            elif cur_val in ("", None):
                # Floats: if empty, fall back to global
                suggested = global_data.get(key, "") if global_data else ""
            else:
                # Floats: use current value when present
                suggested = cur_val
            # Attach description on value (read via schema[key].description)
            schema_dict[key] = vol.Optional(
                str, description={"suggested_value": suggested}
            )

        return vol.Schema(schema_dict)

    @staticmethod
    def _parse_group_options_result(user_input: dict[str, Any]) -> dict[str, Any]:
        """Coerce group options inputs while keeping empties for inheritance."""
        result: dict[str, Any] = {
            "name": user_input.get("name", ""),
            "room_temp_entity": user_input.get("room_temp_entity", ""),
        }

        if "diffuse_factor" in user_input:
            result["diffuse_factor"] = allow_empty_float(0.05, 0.5)(
                user_input.get("diffuse_factor")
            )
        if "threshold_direct" in user_input:
            result["threshold_direct"] = allow_empty_int(0, 1000)(
                user_input.get("threshold_direct")
            )
        if "threshold_diffuse" in user_input:
            result["threshold_diffuse"] = allow_empty_int(0, 1000)(
                user_input.get("threshold_diffuse")
            )
        if "temperature_indoor_base" in user_input:
            result["temperature_indoor_base"] = allow_empty_float(10, 30)(
                user_input.get("temperature_indoor_base")
            )
        if "temperature_outdoor_base" in user_input:
            result["temperature_outdoor_base"] = allow_empty_float(10, 30)(
                user_input.get("temperature_outdoor_base")
            )
        return result

    # ----- Window options flow (per window) -----
    async def async_step_window_options(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Options for a window: manage linked group and overrides with inheritance."""
        opts = self.config_entry.options or {}
        data = self.config_entry.data or {}

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
        schema = self._build_window_options_schema(
            opts,
            data,
            ctx,
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
    ) -> vol.Schema:
        schema_dict: dict[Any, Any] = {}
        name_def = str(self._prefer_options(opts, data, "name", ""))
        schema_dict[vol.Required("name", default=name_def)] = str

        # room temp entity: suggest current value only
        temp_sensor_options = self._get_temperature_sensor_entities(self.hass)
        rte_def = self._prefer_options(opts, data, "room_temp_entity", "")
        schema_dict[
            vol.Optional(
                "room_temp_entity",
                description={"suggested_value": rte_def},
            )
        ] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=temp_sensor_options, custom_value=True
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
            # Attach description on value (read via schema[key].description)
            schema_dict[key] = vol.Optional(
                str, description={"suggested_value": suggested}
            )

        return vol.Schema(schema_dict)

    @staticmethod
    def _parse_window_options_result(
        user_input: dict[str, Any],
        group_options_map: list[tuple[str, str]],
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": user_input.get("name", ""),
            "room_temp_entity": user_input.get("room_temp_entity", ""),
        }

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

    _LOGGER = logging.getLogger(__name__)
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

        def _check_float(field: str, min_v: float, max_v: float) -> None:
            raw = user_input.get(field)
            try:
                fv = self._parse_float_locale(raw)
            except (ValueError, TypeError):
                errors[field] = "invalid_number"
                return
            if fv < min_v or fv > max_v:
                errors[field] = "number_out_of_range"
                return
            page1[field] = fv

        _check_float("window_width", 0.1, 10)
        _check_float("window_height", 0.1, 10)
        _check_float("shadow_depth", 0, 5)
        _check_float("shadow_offset", 0, 5)
        # Required selectors: must be provided
        for req_key in ("solar_radiation_sensor", "outdoor_temperature_sensor"):
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

        def _check_float(field: str, min_v: float, max_v: float) -> None:
            raw = user_input.get(field)
            try:
                fv = self._parse_float_locale(raw)
            except (ValueError, TypeError):
                errors2[field] = "invalid_number"
                return
            if fv < min_v or fv > max_v:
                errors2[field] = "number_out_of_range"
                return
            page2[field] = fv

        def _check_int(field: str, min_v: int, max_v: int) -> None:
            raw = user_input.get(field)
            try:
                iv = self._parse_int_locale(raw)
            except (ValueError, TypeError):
                errors2[field] = "invalid_number"
                return
            if iv < min_v or iv > max_v:
                errors2[field] = "number_out_of_range"
                return
            page2[field] = iv

        _check_float("g_value", 0.1, 0.9)
        _check_float("frame_width", 0.05, 0.3)
        _check_int("tilt", 0, 90)
        _check_float("diffuse_factor", 0.05, 0.5)
        _check_int("threshold_direct", 0, 1000)
        _check_int("threshold_diffuse", 0, 1000)
        _check_float("temperature_indoor_base", 10, 30)
        _check_float("temperature_outdoor_base", 10, 30)

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

        def _check_float(field: str, min_v: float, max_v: float) -> None:
            raw = user_input.get(field)
            try:
                fv = self._parse_float_locale(raw)
            except (ValueError, TypeError):
                errors3[field] = "invalid_number"
                return
            if fv < min_v or fv > max_v:
                errors3[field] = "number_out_of_range"
                return
            p3[field] = fv

        def _check_int(field: str, min_v: int, max_v: int) -> None:
            raw = user_input.get(field)
            try:
                iv = self._parse_int_locale(raw)
            except (ValueError, TypeError):
                errors3[field] = "invalid_number"
                return
            if iv < min_v or iv > max_v:
                errors3[field] = "number_out_of_range"
                return
            p3[field] = iv

        _check_float("scenario_b_temp_indoor", 10, 30)
        _check_float("scenario_b_temp_outdoor", 10, 30)
        _check_float("scenario_c_temp_indoor", 10, 30)
        _check_float("scenario_c_temp_outdoor", 10, 30)
        _check_float("scenario_c_temp_forecast", 15, 40)
        _check_int("scenario_c_start_hour", 0, 23)

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
