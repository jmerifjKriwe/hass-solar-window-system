"""Config flow for Solar Window System."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import DOMAIN


class SolarWindowConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Solar Window System."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle a flow initiated by the user."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        if user_input is not None:
            # Remove optional entity selectors if None (HA does not accept None as entity_id)
            cleaned_input = dict(user_input)
            for key in ("weather_warning_sensor", "forecast_temperature_sensor"):
                if cleaned_input.get(key) is None:
                    cleaned_input.pop(key, None)
            return self.async_create_entry(
                title="Solar Window System", data=cleaned_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("solar_radiation_sensor"): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Required("outdoor_temperature_sensor"): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="sensor", device_class="temperature"
                        )
                    ),
                    vol.Required("update_interval", default=5): vol.All(
                        vol.Coerce(int), vol.Range(min=1)
                    ),
                    vol.Required("min_solar_radiation", default=50): vol.All(
                        vol.Coerce(float), vol.Range(min=0)
                    ),
                    vol.Required("min_sun_elevation", default=10): vol.All(
                        vol.Coerce(float), vol.Range(min=0, max=90)
                    ),
                    vol.Optional("weather_warning_sensor"): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="binary_sensor")
                    ),
                    vol.Optional(
                        "forecast_temperature_sensor"
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="sensor", device_class="temperature"
                        )
                    ),
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return SolarWindowOptionsFlowHandler(config_entry)


class SolarWindowOptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize the options flow."""
        self.config_entry = config_entry

    def _get_value(self, key: str, default=None):
        """Get a value from options."""
        return self.config_entry.options.get(key, default)

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            updated_data = self.config_entry.options.copy()
            updated_data.update(user_input)

            # Process deletion checkboxes
            if updated_data.get("delete_weather_warning_sensor"):
                updated_data["weather_warning_sensor"] = None
            if updated_data.get("delete_forecast_temperature_sensor"):
                updated_data["forecast_temperature_sensor"] = None

            # Remove checkbox fields before saving
            updated_data.pop("delete_weather_warning_sensor", None)
            updated_data.pop("delete_forecast_temperature_sensor", None)

            # Remove optional entity selectors if None (HA does not accept None as entity_id)
            for key in ("weather_warning_sensor", "forecast_temperature_sensor"):
                if updated_data.get(key) is None:
                    updated_data.pop(key, None)

            return self.async_create_entry(title="", data=updated_data)

        weather_sensor_val = self._get_value("weather_warning_sensor")
        forecast_sensor_val = self._get_value("forecast_temperature_sensor")

        fields = {}
        fields[
            vol.Required(
                "solar_radiation_sensor",
                default=self._get_value("solar_radiation_sensor"),
            )
        ] = selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor"))
        fields[
            vol.Required(
                "outdoor_temperature_sensor",
                default=self._get_value("outdoor_temperature_sensor"),
            )
        ] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
        )
        fields[
            vol.Required(
                "update_interval",
                default=self._get_value("update_interval", 5),
            )
        ] = vol.All(vol.Coerce(int), vol.Range(min=1))
        fields[
            vol.Required(
                "min_solar_radiation",
                default=self._get_value("min_solar_radiation", 50),
            )
        ] = vol.All(vol.Coerce(float), vol.Range(min=0))
        fields[
            vol.Required(
                "min_sun_elevation",
                default=self._get_value("min_sun_elevation", 10),
            )
        ] = vol.All(vol.Coerce(float), vol.Range(min=0, max=90))

        # Optional: weather_warning_sensor
        if weather_sensor_val is not None:
            fields[
                vol.Optional("weather_warning_sensor", default=weather_sensor_val)
            ] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain="binary_sensor")
            )
            fields[vol.Optional("delete_weather_warning_sensor", default=False)] = bool
        else:
            fields[vol.Optional("weather_warning_sensor")] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain="binary_sensor")
            )

        # Optional: forecast_temperature_sensor
        if forecast_sensor_val is not None:
            fields[
                vol.Optional("forecast_temperature_sensor", default=forecast_sensor_val)
            ] = selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="sensor", device_class="temperature"
                )
            )
            fields[
                vol.Optional("delete_forecast_temperature_sensor", default=False)
            ] = bool
        else:
            fields[vol.Optional("forecast_temperature_sensor")] = (
                selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="temperature"
                    )
                )
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(fields),
        )
