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
    async def async_step_global_init(self, user_input=None):
        """Handle the global_init step."""
        # TODO: Implement the actual logic for the global_init step
        return self.async_show_form(step_id="global_init")

    async def async_step_window_init(self, user_input=None):
        """Handle the window_init step."""
        # TODO: Implement the actual logic for the window_init step
        return self.async_show_form(step_id="window_init")

    async def async_step_group_init(self, user_input=None):
        """Handle the group_init step."""
        # TODO: Implement the actual logic for the group_init step
        return self.async_show_form(step_id="group_init")

    VERSION = 1
    _user_input = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        if config_entry.data.get(CONF_ENTRY_TYPE) == "window":
            return SolarWindowOptionsFlowWindow(config_entry)
        return SolarWindowOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step of the config flow, allowing selection of entry type."""
        global_config_exists = any(
            entry.data.get(CONF_ENTRY_TYPE) == "global"
            for entry in self._async_current_entries()
        )

        if user_input is not None:
            entry_type = user_input[CONF_ENTRY_TYPE]
            if entry_type == "global":
                if global_config_exists:
                    return self.async_abort(reason="only_one_global")
                # Canonical step ID: global_init
                return await self.async_step_global_init()
            if entry_type == "window":
                # Canonical step ID: window_init
                return await self.async_step_window_init()
            if entry_type == "group":
                # Canonical step ID: group_init
                return await self.async_step_group_init()

        choices = ["global"] if not global_config_exists else ["window", "group"]

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_ENTRY_TYPE): vol.In(choices)}),
        )

    async def async_step_global_scenarios(self, user_input=None):
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
            step_id="global_scenarios",
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
        """Entry point for the options flow."""
        return await self.async_step_window_init(user_input)

    async def async_step_window_init(self, user_input=None):
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
                    vol.Coerce(float), vol.Range(min=-90, max=0)
                ),
                vol.Optional("azimuth_max"): vol.All(
                    vol.Coerce(float), vol.Range(min=0, max=90)
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
            step_id="window_init",
            data_schema=self.add_suggested_values_to_schema(schema, options),
            errors=errors,
            description_placeholders={
                "tilt": str(global_defaults.get("tilt", 90)),
                "g_value": str(global_defaults.get("g_value", 0.5)),
                "frame_width": str(global_defaults.get("frame_width", 0.125)),
                "name": self.config_entry.data.get("name", "Unknown Window"),
            },
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
                vol.Optional("diffuse_factor"): vol.All(
                    vol.Coerce(float), vol.Range(min=0.05, max=0.5)
                ),
                vol.Optional("threshold_direct"): vol.All(
                    vol.Coerce(float), vol.Range(min=0)
                ),
                vol.Optional("threshold_diffuse"): vol.All(
                    vol.Coerce(float), vol.Range(min=0)
                ),
                vol.Optional("indoor_base"): vol.All(
                    vol.Coerce(float), vol.Range(min=10, max=30)
                ),
                vol.Optional("outdoor_base"): vol.All(
                    vol.Coerce(float), vol.Range(min=10, max=30)
                ),
                vol.Optional("scenario_b_temp_indoor_threshold"): vol.Coerce(float),
                vol.Optional("scenario_b_temp_outdoor_threshold"): vol.Coerce(float),
                vol.Optional("scenario_c_temp_forecast_threshold"): vol.Coerce(float),
                vol.Optional("scenario_c_temp_indoor_threshold"): vol.Coerce(float),
                vol.Optional("scenario_c_temp_outdoor_threshold"): vol.Coerce(float),
                vol.Optional("scenario_c_start_hour"): vol.All(
                    vol.Coerce(int), vol.Range(min=0, max=23)
                ),
            }
        )

        return self.async_show_form(
            step_id="window_overrides",
            data_schema=self.add_suggested_values_to_schema(schema, options),
            last_step="init",
        )
