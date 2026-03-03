"""Configuration storage for the Solar Window System integration."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    CONF_GLOBAL,
    CONF_GROUPS,
    CONF_WINDOWS,
    STORAGE_VERSION,
    STORAGE_KEY,
)


class ConfigStore:
    """Handle storage of configuration data."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the ConfigStore.

        Args:
            hass: The Home Assistant instance.
        """
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.version = STORAGE_VERSION

    async def async_load(self) -> dict:
        """Load configuration from storage.

        Returns:
            The configuration dictionary. Returns an empty config structure
            if no configuration has been saved yet.
        """
        data = await self._store.async_load()
        if data is None:
            return self._get_empty_config()
        return data

    async def async_save(self, config: dict) -> None:
        """Save configuration to storage.

        Args:
            config: The configuration dictionary to save.
        """
        await self._store.async_save(config)

    def _get_empty_config(self) -> dict:
        """Return an empty configuration structure.

        Returns:
            A dictionary with the basic structure but no data.
        """
        return {
            "version": self.version,
            CONF_GLOBAL: {},
            CONF_GROUPS: {},
            CONF_WINDOWS: {},
        }
