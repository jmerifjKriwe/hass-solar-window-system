# coding: utf-8
"""Config flow for Solar Window System."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import DOMAIN, CONF_ENTRY_TYPE


def _get_schema(options: dict | None = None) -> vol.Schema:
    if options is None:
        options = {}

    fields = {
        vol.Required(
            "solar_radiation_sensor",
            default=options.get("solar_radiation_sensor"),
        ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
        vol.Required(
            "outdoor_temperature_sensor",
            default=options.get("outdoor_temperature_sensor"),
        ): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
        ),
        vol.Required(
            "update_interval", default=options.get("update_interval", 5)
        ): vol.All(vol.Coerce(int), vol.Range(min=1)),
        vol.Required(
            "min_solar_radiation", default=options.get("min_solar_radiation", 50)
        ): vol.All(vol.Coerce(float), vol.Range(min=0)),
        vol.Required(
            "min_sun_elevation", default=options.get("min_sun_elevation", 10)
        ): vol.All(vol.Coerce(float), vol.Range(min=0, max=90)),
    }

    weather_sensor = options.get("weather_warning_sensor")
    fields[
        vol.Optional(
            "weather_warning_sensor",
            default=weather_sensor if weather_sensor else vol.UNDEFINED,
        )
    ] = selector.EntitySelector(selector.EntitySelectorConfig(domain="binary_sensor"))
    if weather_sensor:
        fields[vol.Optional("delete_weather_warning_sensor", default=False)] = bool

    forecast_sensor = options.get("forecast_temperature_sensor")
    fields[
        vol.Optional(
            "forecast_temperature_sensor",
            default=forecast_sensor if forecast_sensor else vol.UNDEFINED,
        )
    ] = selector.EntitySelector(
        selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
    )
    if forecast_sensor:
        fields[vol.Optional("delete_forecast_temperature_sensor", default=False)] = bool

    return vol.Schema(fields)


class SolarWindowConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    _user_input = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return SolarWindowOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        global_config_exists = any(
            entry.data.get(CONF_ENTRY_TYPE) == "global"
            for entry in self._async_current_entries()
        )

        if user_input is not None:
            entry_type = user_input[CONF_ENTRY_TYPE]
            if entry_type == "global":
                if global_config_exists:
                    return self.async_abort(reason="only_one_global")
                return await self.async_step_global()
            elif entry_type == "window":
                return await self.async_step_add_window()
            elif entry_type == "group":
                return await self.async_step_add_group()

        choices = ["global"] if not global_config_exists else ["window", "group"]

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_ENTRY_TYPE): vol.In(choices)}),
        )

    async def async_step_global(self, user_input=None):
        if user_input is not None:
            self._user_input.update(user_input)
            return await self.async_step_thresholds()

        return self.async_show_form(
            step_id="global",
            data_schema=_get_schema(self._user_input),
            last_step="user",
        )

    async def async_step_thresholds(self, user_input=None):
        if user_input is not None:
            self._user_input.update(user_input)
            return await self.async_step_scenarios()

        return self.async_show_form(
            step_id="thresholds",
            data_schema=vol.Schema(
                {
                    vol.Required("g_value", default=0.5): vol.All(
                        vol.Coerce(float), vol.Range(min=0.1, max=0.9)
                    ),
                    vol.Required("frame_width", default=0.125): vol.All(
                        vol.Coerce(float), vol.Range(min=0.05, max=0.3)
                    ),
                    vol.Required("tilt", default=90): vol.All(
                        vol.Coerce(float), vol.Range(min=0, max=90)
                    ),
                    vol.Required("diffuse_factor", default=0.15): vol.All(
                        vol.Coerce(float), vol.Range(min=0.05, max=0.5)
                    ),
                    vol.Required("threshold_direct", default=200): vol.All(
                        vol.Coerce(float), vol.Range(min=0)
                    ),
                    vol.Required("threshold_diffuse", default=150): vol.All(
                        vol.Coerce(float), vol.Range(min=0)
                    ),
                    vol.Required("indoor_base", default=23.0): vol.All(
                        vol.Coerce(float), vol.Range(min=10, max=30)
                    ),
                    vol.Required("outdoor_base", default=19.5): vol.All(
                        vol.Coerce(float), vol.Range(min=10, max=30)
                    ),
                }
            ),
            last_step="global",
        )

    async def async_step_scenarios(self, user_input=None):
        if user_input is not None:
            self._user_input.update(user_input)
            self._user_input[CONF_ENTRY_TYPE] = "global"

            if self._user_input.get("delete_weather_warning_sensor"):
                self._user_input.pop("weather_warning_sensor", None)
            if self._user_input.get("delete_forecast_temperature_sensor"):
                self._user_input.pop("forecast_temperature_sensor", None)

            self._user_input.pop("delete_weather_warning_sensor", None)
            self._user_input.pop("delete_forecast_temperature_sensor", None)

            return self.async_create_entry(
                title="Global Configuration",
                data={CONF_ENTRY_TYPE: "global"},
                options=self._user_input,
            )

        return self.async_show_form(
            step_id="scenarios",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "scenario_b_temp_indoor_threshold", default=23.5
                    ): vol.All(vol.Coerce(float), vol.Range(min=18, max=30)),
                    vol.Required(
                        "scenario_b_temp_outdoor_threshold", default=25.5
                    ): vol.All(vol.Coerce(float), vol.Range(min=18, max=35)),
                    vol.Required(
                        "scenario_c_temp_forecast_threshold", default=28.5
                    ): vol.All(vol.Coerce(float), vol.Range(min=20, max=40)),
                    vol.Required(
                        "scenario_c_temp_indoor_threshold", default=21.5
                    ): vol.All(vol.Coerce(float), vol.Range(min=18, max=30)),
                    vol.Required(
                        "scenario_c_temp_outdoor_threshold", default=24.0
                    ): vol.All(vol.Coerce(float), vol.Range(min=18, max=35)),
                    vol.Required("scenario_c_start_hour", default=9): vol.All(
                        vol.Coerce(int), vol.Range(min=0, max=23)
                    ),
                }
            ),
            last_step="thresholds",
        )

    async def async_step_add_window(self, user_input=None):
        global_entry = next(
            (
                entry
                for entry in self._async_current_entries()
                if entry.data.get(CONF_ENTRY_TYPE) == "global"
            ),
            None,
        )
        defaults = global_entry.options if global_entry else {}

        if user_input is not None:
            self._user_input = user_input.copy()
            self._user_input[CONF_ENTRY_TYPE] = "window"
            for key in ["tilt", "g_value", "frame_width"]:
                if key in self._user_input and self._user_input[key] == defaults.get(
                    key
                ):
                    self._user_input.pop(key)
            return await self.async_step_window_overrides()

        return self.async_show_form(
            step_id="add_window",
            data_schema=vol.Schema(
                {
                    vol.Required("name"): str,
                    vol.Required("azimuth"): vol.All(
                        vol.Coerce(float), vol.Range(min=0, max=360)
                    ),
                    vol.Required("azimuth_min"): vol.All(
                        vol.Coerce(float), vol.Range(min=-180, max=180)
                    ),
                    vol.Required("azimuth_max"): vol.All(
                        vol.Coerce(float), vol.Range(min=-180, max=180)
                    ),
                    vol.Required("elevation_min"): vol.All(
                        vol.Coerce(float), vol.Range(min=0, max=90)
                    ),
                    vol.Required("elevation_max"): vol.All(
                        vol.Coerce(float), vol.Range(min=0, max=90)
                    ),
                    vol.Required("width"): vol.All(
                        vol.Coerce(float), vol.Range(min=0.1, max=10)
                    ),
                    vol.Required("height"): vol.All(
                        vol.Coerce(float), vol.Range(min=0.1, max=10)
                    ),
                    vol.Required("shadow_depth"): vol.All(
                        vol.Coerce(float), vol.Range(min=0, max=5)
                    ),
                    vol.Required("shadow_offset"): vol.All(
                        vol.Coerce(float), vol.Range(min=0, max=5)
                    ),
                    vol.Required("room_temp_entity"): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="sensor", device_class="temperature"
                        )
                    ),
                    vol.Optional("tilt", default=defaults.get("tilt")): vol.All(
                        vol.Coerce(float), vol.Range(min=0, max=90)
                    ),
                    vol.Optional("g_value", default=defaults.get("g_value")): vol.All(
                        vol.Coerce(float), vol.Range(min=0.1, max=0.9)
                    ),
                    vol.Optional(
                        "frame_width", default=defaults.get("frame_width")
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.05, max=0.3)),
                }
            ),
            last_step="user",
        )

    async def async_step_window_overrides(self, user_input=None):
        global_entry = next(
            (
                entry
                for entry in self._async_current_entries()
                if entry.data.get(CONF_ENTRY_TYPE) == "global"
            ),
            None,
        )
        defaults = global_entry.options if global_entry else {}

        if user_input is not None:
            clean = {
                k: v
                for k, v in user_input.items()
                if v is not None and defaults.get(k) != v
            }
            self._user_input.update(clean)
            return self.async_create_entry(
                title=self._user_input["name"], data=self._user_input, options={}
            )

        return self.async_show_form(
            step_id="window_overrides",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "diffuse_factor", default=defaults.get("diffuse_factor")
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.05, max=0.5)),
                    vol.Optional(
                        "threshold_direct", default=defaults.get("threshold_direct")
                    ): vol.All(vol.Coerce(float), vol.Range(min=0)),
                    vol.Optional(
                        "threshold_diffuse", default=defaults.get("threshold_diffuse")
                    ): vol.All(vol.Coerce(float), vol.Range(min=0)),
                    vol.Optional(
                        "indoor_base", default=defaults.get("indoor_base")
                    ): vol.All(vol.Coerce(float), vol.Range(min=10, max=30)),
                    vol.Optional(
                        "outdoor_base", default=defaults.get("outdoor_base")
                    ): vol.All(vol.Coerce(float), vol.Range(min=10, max=30)),
                    vol.Optional(
                        "scenario_b_temp_indoor_offset",
                        default=defaults.get("scenario_b_temp_indoor_offset"),
                    ): vol.Coerce(float),
                    vol.Optional(
                        "scenario_b_temp_outdoor_offset",
                        default=defaults.get("scenario_b_temp_outdoor_offset"),
                    ): vol.Coerce(float),
                    vol.Optional(
                        "scenario_c_temp_forecast_threshold",
                        default=defaults.get("scenario_c_temp_forecast_threshold"),
                    ): vol.Coerce(float),
                    vol.Optional(
                        "scenario_c_temp_indoor_threshold",
                        default=defaults.get("scenario_c_temp_indoor_threshold"),
                    ): vol.Coerce(float),
                    vol.Optional(
                        "scenario_c_temp_outdoor_threshold",
                        default=defaults.get("scenario_c_temp_outdoor_threshold"),
                    ): vol.Coerce(float),
                    vol.Optional(
                        "scenario_c_start_hour",
                        default=defaults.get("scenario_c_start_hour"),
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=23)),
                }
            ),
            last_step="add_window",
        )

    async def async_step_add_group(self, user_input=None):
        if user_input is not None:
            user_input[CONF_ENTRY_TYPE] = "group"
            return self.async_create_entry(
                title=user_input["name"], data=user_input, options={}
            )

        return self.async_show_form(
            step_id="add_group",
            data_schema=vol.Schema(
                {
                    vol.Required("name"): str,
                    vol.Required("windows"): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="cover", multiple=True)
                    ),
                }
            ),
            last_step="user",
        )


class SolarWindowOptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize the options flow."""
        self.config_entry = config_entry
        self._user_input = dict(config_entry.options)

    async def async_step_init(self, user_input=None):
        """Manage the first step of the options flow."""
        if user_input is not None:
            self._user_input.update(user_input)
            return await self.async_step_thresholds()

        return self.async_show_form(
            step_id="init", data_schema=_get_schema(self._user_input)
        )

    async def async_step_thresholds(self, user_input=None):
        """Manage the thresholds step of the options flow."""
        if user_input is not None:
            self._user_input.update(user_input)
            return await self.async_step_scenarios()

        options = self._user_input
        threshold_schema = vol.Schema(
            {
                vol.Required(
                    "g_value", default=options.get("g_value", 0.5)
                ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=0.9)),
                vol.Required(
                    "frame_width", default=options.get("frame_width", 0.125)
                ): vol.All(vol.Coerce(float), vol.Range(min=0.05, max=0.3)),
                vol.Required("tilt", default=options.get("tilt", 90)): vol.All(
                    vol.Coerce(float), vol.Range(min=0, max=90)
                ),
                vol.Required(
                    "diffuse_factor", default=options.get("diffuse_factor", 0.15)
                ): vol.All(vol.Coerce(float), vol.Range(min=0.05, max=0.5)),
                vol.Required(
                    "threshold_direct", default=options.get("threshold_direct", 200)
                ): vol.All(vol.Coerce(float), vol.Range(min=0)),
                vol.Required(
                    "threshold_diffuse", default=options.get("threshold_diffuse", 150)
                ): vol.All(vol.Coerce(float), vol.Range(min=0)),
                vol.Required(
                    "indoor_base", default=options.get("indoor_base", 23.0)
                ): vol.All(vol.Coerce(float), vol.Range(min=10, max=30)),
                vol.Required(
                    "outdoor_base", default=options.get("outdoor_base", 19.5)
                ): vol.All(vol.Coerce(float), vol.Range(min=10, max=30)),
            }
        )
        return self.async_show_form(step_id="thresholds", data_schema=threshold_schema)

    async def async_step_scenarios(self, user_input=None):
        """Manage the scenarios step of the options flow."""
        if user_input is not None:
            self._user_input.update(user_input)

            if self._user_input.get("delete_weather_warning_sensor"):
                self._user_input.pop("weather_warning_sensor", None)
            if self._user_input.get("delete_forecast_temperature_sensor"):
                self._user_input.pop("forecast_temperature_sensor", None)

            self._user_input.pop("delete_weather_warning_sensor", None)
            self._user_input.pop("delete_forecast_temperature_sensor", None)

            return self.async_create_entry(title="", data=self._user_input)

        options = self._user_input
        scenarios_schema = vol.Schema(
            {
                vol.Required(
                    "scenario_b_temp_indoor_threshold",
                    default=options.get("scenario_b_temp_indoor_threshold", 23.5),
                ): vol.All(vol.Coerce(float), vol.Range(min=18, max=30)),
                vol.Required(
                    "scenario_b_temp_outdoor_threshold",
                    default=options.get("scenario_b_temp_outdoor_threshold", 25.5),
                ): vol.All(vol.Coerce(float), vol.Range(min=18, max=35)),
                vol.Required(
                    "scenario_c_temp_forecast_threshold",
                    default=options.get("scenario_c_temp_forecast_threshold", 28.5),
                ): vol.All(vol.Coerce(float), vol.Range(min=20, max=40)),
                vol.Required(
                    "scenario_c_temp_indoor_threshold",
                    default=options.get("scenario_c_temp_indoor_threshold", 21.5),
                ): vol.All(vol.Coerce(float), vol.Range(min=18, max=30)),
                vol.Required(
                    "scenario_c_temp_outdoor_threshold",
                    default=options.get("scenario_c_temp_outdoor_threshold", 24.0),
                ): vol.All(vol.Coerce(float), vol.Range(min=18, max=35)),
                vol.Required(
                    "scenario_c_start_hour",
                    default=options.get("scenario_c_start_hour", 9),
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=23)),
            }
        )
        return self.async_show_form(
            step_id="scenarios", data_schema=scenarios_schema
        )