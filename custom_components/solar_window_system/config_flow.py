"""Config flow for Solar Window System."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import DOMAIN


def _get_schema(options: dict | None = None) -> vol.Schema:
    """Return the data schema for the config and options flow."""
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
    """Config flow for Solar Window System."""

    VERSION = 1
    _user_input = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initiated by the user."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        if user_input is not None:
            self._user_input.update(user_input)
            return await self.async_step_thresholds()

        return self.async_show_form(step_id="user", data_schema=_get_schema())

    async def async_step_thresholds(self, user_input=None):
        """Handle the thresholds step."""
        if user_input is not None:
            self._user_input.update(user_input)
            return await self.async_step_scenarios()

        return self.async_show_form(
            step_id="thresholds",
            data_schema=vol.Schema(
                {
                    vol.Required("threshold_direct", default=200): vol.All(
                        vol.Coerce(float), vol.Range(min=0)
                    ),
                    vol.Required("threshold_diffuse", default=150): vol.All(
                        vol.Coerce(float), vol.Range(min=0)
                    ),
                    vol.Required("diffuse_factor", default=0.5): vol.All(
                        vol.Coerce(float), vol.Range(min=0, max=1)
                    ),
                    vol.Required("indoor_base", default=23.0): vol.All(
                        vol.Coerce(float), vol.Range(min=10, max=30)
                    ),
                    vol.Required("outdoor_base", default=19.5): vol.All(
                        vol.Coerce(float), vol.Range(min=10, max=30)
                    ),
                }
            ),
        )

    async def async_step_scenarios(self, user_input=None):
        """Handle the scenarios step."""
        if user_input is not None:
            self._user_input.update(user_input)
            return self.async_create_entry(
                title="Solar Window System", data={}, options=self._user_input
            )

        return self.async_show_form(
            step_id="scenarios",
            data_schema=vol.Schema(
                {
                    vol.Required("enabled_scenario_b", default=False): bool,
                    vol.Required("scenario_b_temp_indoor_offset", default=0.5): vol.All(
                        vol.Coerce(float), vol.Range(min=0, max=5)
                    ),
                    vol.Required("scenario_b_temp_outdoor_offset", default=6.0): vol.All(
                        vol.Coerce(float), vol.Range(min=0, max=10)
                    ),
                    vol.Required("scenario_c_enable", default=False): bool,
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
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow handler for this config entry."""
        flow = SolarWindowOptionsFlowHandler()
        flow._config_entry = config_entry
        return flow


class SolarWindowOptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self):
        """Initialize the options flow."""
        self._config_entry = None
        self._user_input = {}

    async def async_step_init(self, user_input=None):
        """Manage the first step of the options flow."""
        if user_input is not None:
            self._user_input.update(user_input)
            return await self.async_step_thresholds()

        return self.async_show_form(
            step_id="init", data_schema=_get_schema(self._config_entry.options)
        )

    async def async_step_thresholds(self, user_input=None):
        """Manage the thresholds step of the options flow."""
        if user_input is not None:
            self._user_input.update(user_input)
            return await self.async_step_scenarios()

        options = self._config_entry.options
        threshold_schema = vol.Schema(
            {
                vol.Required(
                    "threshold_direct", default=options.get("threshold_direct", 200)
                ): vol.All(vol.Coerce(float), vol.Range(min=0)),
                vol.Required(
                    "threshold_diffuse", default=options.get("threshold_diffuse", 150)
                ): vol.All(vol.Coerce(float), vol.Range(min=0)),
                vol.Required(
                    "diffuse_factor", default=options.get("diffuse_factor", 0.5)
                ): vol.All(vol.Coerce(float), vol.Range(min=0, max=1)),
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

        options = self._config_entry.options
        scenarios_schema = vol.Schema(
            {
                vol.Required(
                    "enabled_scenario_b",
                    default=options.get("enabled_scenario_b", False),
                ): bool,
                vol.Required(
                    "scenario_b_temp_indoor_offset",
                    default=options.get("scenario_b_temp_indoor_offset", 0.5),
                ): vol.All(vol.Coerce(float), vol.Range(min=0, max=5)),
                vol.Required(
                    "scenario_b_temp_outdoor_offset",
                    default=options.get("scenario_b_temp_outdoor_offset", 6.0),
                ): vol.All(vol.Coerce(float), vol.Range(min=0, max=10)),
                vol.Required(
                    "scenario_c_enable",
                    default=options.get("scenario_c_enable", False),
                ): bool,
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