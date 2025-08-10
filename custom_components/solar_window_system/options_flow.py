"""Options flow for Solar Window System integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector


class SolarWindowSystemOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Solar Window System."""

    def __init__(self) -> None:
        """Initialize the options flow."""
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
        """Start options flow at page 1 (basic)."""
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
            # For entity selector, None renders as empty/cleared; map "" -> None
            return None if v in ("", None) else v

        def _sel_default_with_fallback(key: str) -> Any:
            # If key explicitly present in options, respect it (including "")
            if key in opts:
                return _sel_default(opts.get(key))
            # Otherwise, fall back to original data for initial display
            return _sel_default(data.get(key, ""))

        defaults = {
            "window_width": str(_g("window_width", "")),
            "window_height": str(_g("window_height", "")),
            "shadow_depth": str(_g("shadow_depth", "")),
            "shadow_offset": str(_g("shadow_offset", "")),
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
                    vol.Optional(
                        "forecast_temperature_sensor",
                        default=defaults["forecast_temperature_sensor"],
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
                        default=defaults["weather_warning_sensor"],
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

        # validate required numerics with per-field errors (accept comma)
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

        page1["forecast_temperature_sensor"] = (
            user_input.get("forecast_temperature_sensor") or ""
        )
        page1["weather_warning_sensor"] = user_input.get("weather_warning_sensor") or ""

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
