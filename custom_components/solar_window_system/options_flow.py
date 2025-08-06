"""Options flow for Solar Window System integration."""

from homeassistant import config_entries
from .const import DOMAIN
from homeassistant.helpers import config_validation as cv
import voluptuous as vol


class SolarWindowSystemOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Solar Window System."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        return self.async_create_entry(title="", data={})
