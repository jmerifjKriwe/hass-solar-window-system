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
                vol.Optional("weather_warning_sensor"): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="binary_sensor"),
                ),
                vol.Optional("forecast_temperature_sensor"): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="temperature"
                    ),
                ),
            }
        )

        if user_input is not None:
            try:
                await self._validate_user_input(user_input)
            except Exception:
                errors["base"] = "invalid_entity"
            else:
                cleaned_input = {k: v for k, v in user_input.items() if v is not None}
                return self.async_create_entry(
                    title="Solar Window System", data=cleaned_input
                )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def _validate_user_input(self, data: dict[str, Any]) -> None:
        """Validate that the selected entities exist."""
        for key in [
            "solar_radiation_sensor",
            "outdoor_temperature_sensor",
            "weather_warning_sensor",
            "forecast_temperature_sensor",
        ]:
            if entity_id := data.get(key):
                if not self.hass.states.get(entity_id):
                    raise vol.Invalid(f"Entity {entity_id} not found")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Get the options flow for this handler."""
        return SolarWindowOptionsFlowHandler(config_entry)


class SolarWindowOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle an options flow for Solar Window System."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        # KORRIGIERT: self.config_entry wird von der Basisklasse geerbt.
        # Die _initial_data werden direkt aus dem übergebenen config_entry erstellt.
        self._initial_data = {**config_entry.data, **config_entry.options}

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage the options after the integration is set up."""
        if user_input is not None:
            updated_options = dict(self.config_entry.options)
            updated_options.update(user_input)

            for key in ["weather_warning_sensor", "forecast_temperature_sensor"]:
                if updated_options.get(key) == "":
                    updated_options.pop(key, None)

            return self.async_create_entry(title="", data=updated_options)

        schema = vol.Schema(
            {
                vol.Required(
                    "update_interval",
                    default=self._initial_data.get("update_interval", 5),
                ): vol.All(vol.Coerce(int), vol.Range(min=1)),
                vol.Required(
                    "solar_radiation_sensor",
                    default=self._initial_data.get("solar_radiation_sensor"),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(
                    "outdoor_temperature_sensor",
                    default=self._initial_data.get("outdoor_temperature_sensor"),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor", device_class="temperature"
                    )
                ),
                vol.Optional(
                    "weather_warning_sensor",
                    default=self._initial_data.get("weather_warning_sensor", ""),
                ): vol.Any(
                    "",
                    selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="binary_sensor")
                    ),
                ),
                vol.Optional(
                    "forecast_temperature_sensor",
                    default=self._initial_data.get("forecast_temperature_sensor", ""),
                ): vol.Any(
                    "",
                    selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain="sensor", device_class="temperature"
                        )
                    ),
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
