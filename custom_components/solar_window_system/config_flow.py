import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, CONF_ENTRY_TYPE
from .const import CONF_WINDOW_NAME


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
        if config_entry.data.get(CONF_ENTRY_TYPE) == "window":
            return SolarWindowOptionsFlowWindow(config_entry)
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
                    vol.Required(
                        CONF_WINDOW_NAME, default=defaults.get(CONF_WINDOW_NAME, "")
                    ): str,
                    vol.Required(
                        "azimuth", default=defaults.get("azimuth", 180)
                    ): vol.All(vol.Coerce(float), vol.Range(min=0, max=360)),
                    vol.Required(
                        "azimuth_min", default=defaults.get("azimuth_min", 0)
                    ): vol.All(vol.Coerce(float), vol.Range(min=-180, max=180)),
                    vol.Required(
                        "azimuth_max", default=defaults.get("azimuth_max", 0)
                    ): vol.All(vol.Coerce(float), vol.Range(min=-180, max=180)),
                    vol.Required(
                        "elevation_min", default=defaults.get("elevation_min", 0)
                    ): vol.All(vol.Coerce(float), vol.Range(min=0, max=90)),
                    vol.Required(
                        "elevation_max", default=defaults.get("elevation_max", 0)
                    ): vol.All(vol.Coerce(float), vol.Range(min=0, max=90)),
                    vol.Required("width", default=defaults.get("width", 1.0)): vol.All(
                        vol.Coerce(float), vol.Range(min=0.1, max=10)
                    ),
                    vol.Required(
                        "height", default=defaults.get("height", 1.0)
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=10)),
                    vol.Required(
                        "shadow_depth", default=defaults.get("shadow_depth", 0)
                    ): vol.All(vol.Coerce(float), vol.Range(min=0, max=5)),
                    vol.Required(
                        "shadow_offset", default=defaults.get("shadow_offset", 0)
                    ): vol.All(vol.Coerce(float), vol.Range(min=0, max=5)),
                    vol.Required(
                        "room_temp_entity", default=defaults.get("room_temp_entity")
                    ): selector.EntitySelector(
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
            self._user_input.update(user_input)
            # Remove defaults
            for key in list(self._user_input.keys()):
                if (
                    self._user_input[key] == defaults.get(key)
                    or self._user_input[key] is None
                ):
                    self._user_input.pop(key)

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
        self.config_entry = config_entry
        self._user_input = dict(config_entry.options)

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            self._user_input.update(user_input)
            return await self.async_step_thresholds()

        return self.async_show_form(
            step_id="init", data_schema=_get_schema(self._user_input)
        )

    async def async_step_thresholds(self, user_input=None):
        if user_input is not None:
            self._user_input.update(user_input)
            return await self.async_step_scenarios()

        options = self._user_input
        return self.async_show_form(
            step_id="thresholds",
            data_schema=vol.Schema(
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
                        "threshold_diffuse",
                        default=options.get("threshold_diffuse", 150),
                    ): vol.All(vol.Coerce(float), vol.Range(min=0)),
                    vol.Required(
                        "indoor_base", default=options.get("indoor_base", 23.0)
                    ): vol.All(vol.Coerce(float), vol.Range(min=10, max=30)),
                    vol.Required(
                        "outdoor_base", default=options.get("outdoor_base", 19.5)
                    ): vol.All(vol.Coerce(float), vol.Range(min=10, max=30)),
                }
            ),
        )

    async def async_step_scenarios(self, user_input=None):
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
        return self.async_show_form(
            step_id="scenarios",
            data_schema=vol.Schema(
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
            ),
        )


class SolarWindowOptionsFlowWindow(config_entries.OptionsFlow):
    """Handle options flow for a window entry."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize the options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.data)

    async def async_step_init(self, user_input=None):
        """Manage the options for a window."""
        # Find the global configuration entry
        global_entry = next(
            (
                entry
                for entry in self.hass.config_entries.async_entries(DOMAIN)
                if entry.data.get(CONF_ENTRY_TYPE) == "global"
            ),
            None,
        )
        global_defaults = global_entry.options if global_entry else {}
        current_config = self.config_entry.data
        errors = {}

        if user_input is not None:
            # Validation logic
            azimuth = user_input.get("azimuth")
            azimuth_min = user_input.get("azimuth_min")
            azimuth_max = user_input.get("azimuth_max")
            elevation_min = user_input.get("elevation_min")
            elevation_max = user_input.get("elevation_max")

            if (
                azimuth_min is not None
                and azimuth is not None
                and azimuth_min > azimuth
            ):
                errors["azimuth_min"] = "min_greater_than_azimuth"
            if (
                azimuth_max is not None
                and azimuth is not None
                and azimuth_max < azimuth
            ):
                errors["azimuth_max"] = "max_less_than_azimuth"
            if (
                azimuth_min is not None
                and azimuth_max is not None
                and azimuth_min > azimuth_max
            ):
                errors["azimuth_min"] = "min_greater_than_max"
                errors["azimuth_max"] = "max_less_than_min"
            if (
                elevation_min is not None
                and elevation_max is not None
                and elevation_min > elevation_max
            ):
                errors["elevation_min"] = "min_greater_than_max"
                errors["elevation_max"] = "max_less_than_min"

            if not errors:
                self.options.update(user_input)
                return await self.async_step_window_overrides()

        # Merge global defaults with current window config to pre-fill the form
        options = {**global_defaults, **current_config}

        schema = vol.Schema(
            {
                vol.Required("name"): str,
                vol.Required("azimuth"): vol.All(
                    vol.Coerce(float), vol.Range(min=0, max=360)
                ),
                vol.Optional("azimuth_min"): vol.All(
                    vol.Coerce(float), vol.Range(min=-180, max=180)
                ),
                vol.Optional("azimuth_max"): vol.All(
                    vol.Coerce(float), vol.Range(min=-180, max=180)
                ),
                vol.Optional("elevation_min"): vol.All(
                    vol.Coerce(float), vol.Range(min=0, max=90)
                ),
                vol.Optional("elevation_max"): vol.All(
                    vol.Coerce(float), vol.Range(min=0, max=90)
                ),
                vol.Required("width"): vol.All(
                    vol.Coerce(float), vol.Range(min=0.1, max=10)
                ),
                vol.Required("height"): vol.All(
                    vol.Coerce(float), vol.Range(min=0.1, max=10)
                ),
                vol.Optional("shadow_depth"): vol.All(
                    vol.Coerce(float), vol.Range(min=0, max=5)
                ),
                vol.Optional("shadow_offset"): vol.All(
                    vol.Coerce(float), vol.Range(min=0, max=5)
                ),
                vol.Required("room_temp_entity"): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="temperature"
                    )
                ),
                vol.Optional("tilt"): vol.All(
                    vol.Coerce(float), vol.Range(min=0, max=90)
                ),
                vol.Optional("g_value"): vol.All(
                    vol.Coerce(float), vol.Range(min=0.1, max=0.9)
                ),
                vol.Optional("frame_width"): vol.All(
                    vol.Coerce(float), vol.Range(min=0.05, max=0.3)
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(schema, options),
            errors=errors,
        )

    async def async_step_window_overrides(self, user_input=None):
        """Manage the override options for a window."""
        global_entry = next(
            (
                entry
                for entry in self.hass.config_entries.async_entries(DOMAIN)
                if entry.data.get(CONF_ENTRY_TYPE) == "global"
            ),
            None,
        )
        global_defaults = global_entry.options if global_entry else {}

        if user_input is not None:
            self.options.update(user_input)

            # Remove keys that are same as global or are empty/None
            for key in list(self.options.keys()):
                if key in [CONF_ENTRY_TYPE, CONF_WINDOW_NAME]:
                    continue

                if (
                    key in global_defaults
                    and self.options.get(key) == global_defaults[key]
                ):
                    del self.options[key]
                elif self.options.get(key) in [None, ""]:
                    del self.options[key]

            # Update the config entry with the new data
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=self.options
            )
            # Reload the integration to apply changes
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)
            # Finish the flow
            return self.async_create_entry(title="", data={})

        # Merge global defaults with current window config to pre-fill the form
        options = {**global_defaults, **self.options}

        schema = vol.Schema(
            {
                vol.Optional("diffuse_factor"): vol.All(vol.Coerce(float), vol.Range(min=0.05, max=0.5)),
                vol.Optional("threshold_direct"): vol.All(vol.Coerce(float), vol.Range(min=0)),
                vol.Optional("threshold_diffuse"): vol.All(vol.Coerce(float), vol.Range(min=0)),
                vol.Optional("indoor_base"): vol.All(vol.Coerce(float), vol.Range(min=10, max=30)),
                vol.Optional("outdoor_base"): vol.All(vol.Coerce(float), vol.Range(min=10, max=30)),
                vol.Optional("scenario_b_temp_indoor_offset"): vol.Coerce(float),
                vol.Optional("scenario_b_temp_outdoor_offset"): vol.Coerce(float),
                vol.Optional("scenario_c_temp_forecast_threshold"): vol.Coerce(float),
                vol.Optional("scenario_c_temp_indoor_threshold"): vol.Coerce(float),
                vol.Optional("scenario_c_temp_outdoor_threshold"): vol.Coerce(float),
                vol.Optional("scenario_c_start_hour"): vol.All(vol.Coerce(int), vol.Range(min=0, max=23)),
            }
        )

        return self.async_show_form(
            step_id="window_overrides",
            data_schema=self.add_suggested_values_to_schema(schema, options),
            last_step="init",
        )
