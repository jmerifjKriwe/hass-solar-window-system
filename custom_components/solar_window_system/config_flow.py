"""Config flow for Solar Window System."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import DOMAIN


# -------------------------------------------------------------------
# HELPER FUNCTION: Central schema definition for config & options flow
# -------------------------------------------------------------------
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


# -------------------------------------------------------------------
# CONFIG FLOW: For initial setup
# -------------------------------------------------------------------
class SolarWindowConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Solar Window System."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle a flow initiated by the user."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        if user_input is not None:
            return self.async_create_entry(
                title="Solar Window System", data={}, options=user_input
            )

        return self.async_show_form(step_id="user", data_schema=_get_schema())

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow handler for this config entry."""

        # --- WORKAROUND: Manually attach config_entry to OptionsFlowHandler ----------
        #
        # Home Assistant does NOT currently support passing the config_entry directly
        # into the constructor of OptionsFlowHandler (as of HA 2025.7).
        #
        # Attempting to use `super().__init__(config_entry)` results in:
        # → TypeError: object.__init__() takes exactly one argument (the instance)
        #
        # Therefore, the config_entry must be manually attached to the instance
        # using a private attribute (_config_entry). This is NOT officially supported,
        # but is the only functional approach at the moment.
        #
        # ⚠️ Important:
        # - `_config_entry` is considered a private/internal attribute.
        # - This implementation may break in a future Home Assistant release
        #   if internal APIs change (e.g., renaming or new constructor support).
        #
        # ✅ What to do when breaking changes are introduced:
        # - If Home Assistant adds official constructor support, replace this:
        #     flow = SolarWindowOptionsFlowHandler()
        #     flow._config_entry = config_entry
        #   with:
        #     return SolarWindowOptionsFlowHandler(config_entry)
        #
        # 🛠️ How to find this later:
        # - Search for "WORKAROUND: Manually attach config_entry" in your codebase
        #
        # 🔗 Reference:
        # https://github.com/home-assistant/core/issues?q=optionsflow+config_entry
        #
        # Last verified working in Home Assistant 2025.7
        # ----------------------------------------------------------------------------

        flow = SolarWindowOptionsFlowHandler()
        flow._config_entry = config_entry
        return flow


# -------------------------------------------------------------------
# OPTIONS FLOW: For editing config later
# -------------------------------------------------------------------
class SolarWindowOptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        config_entry = self._config_entry

        if user_input is not None:
            updated_data = config_entry.options.copy()
            updated_data.update(user_input)

            if updated_data.get("delete_weather_warning_sensor"):
                updated_data.pop("weather_warning_sensor", None)
            if updated_data.get("delete_forecast_temperature_sensor"):
                updated_data.pop("forecast_temperature_sensor", None)

            updated_data.pop("delete_weather_warning_sensor", None)
            updated_data.pop("delete_forecast_temperature_sensor", None)

            return self.async_create_entry(title="", data=updated_data)

        return self.async_show_form(
            step_id="init", data_schema=_get_schema(config_entry.options)
        )
