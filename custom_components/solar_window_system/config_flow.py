# /config/custom_components/solar_window_system/config_flow.py

import logging
from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class SolarWindowConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Solar Window System."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors = {}

        if user_input is not None:
            # User has filled out the form, create the config entry
            return self.async_create_entry(title="Solar Window System", data=user_input)

        # Show the form to the user
        data_schema = vol.Schema(
            {
                vol.Required("solar_radiation_sensor"): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor"),
                ),
                vol.Required("outdoor_temperature_sensor"): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="temperature"
                    ),
                ),
                # This is the new optional field
                vol.Optional("weather_warning_sensor"): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="binary_sensor"),
                ),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Get the options flow for this handler."""
        return SolarWindowOptionsFlowHandler(config_entry)


class SolarWindowOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle an options flow for Solar Window System."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        # Combine initial data and subsequent options
        self.data = {**config_entry.data, **config_entry.options}

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage the options."""
        if user_input is not None:
            # Merge new options with existing data
            self.data.update(user_input)
            return self.async_create_entry(title="", data=self.data)

        # Build schema, using existing values as defaults
        schema = vol.Schema(
            {
                vol.Required(
                    "update_interval",
                    default=self.data.get("update_interval", 5),
                ): vol.All(vol.Coerce(int), vol.Range(min=1)),
                vol.Required(
                    "solar_radiation_sensor",
                    default=self.data.get("solar_radiation_sensor"),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(
                    "outdoor_temperature_sensor",
                    default=self.data.get("outdoor_temperature_sensor"),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="temperature"
                    )
                ),
                vol.Optional(
                    "weather_warning_sensor",
                    default=self.data.get("weather_warning_sensor"),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="binary_sensor")
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
