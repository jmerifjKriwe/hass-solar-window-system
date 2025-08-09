"""Options flow for Solar Window System integration."""

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry


class SolarWindowSystemOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Solar Window System."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, _user_input: dict | None = None
    ) -> config_entries.ConfigFlowResult:
        """Start and immediately finalize options with no extra fields."""
        return self.async_create_entry(title="", data={})
