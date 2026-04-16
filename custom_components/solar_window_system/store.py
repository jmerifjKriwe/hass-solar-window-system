"""Storage for Solar Window System overrides.

This module only handles persistent storage of user overrides
for thresholds and scenarios. Main configuration is stored
in the Config Entry (via Config Flow).
"""

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    CONF_OVERRIDES,
    STORAGE_KEY,
    STORAGE_VERSION,
)


class ConfigStore:
    """Handle storage of override data only.

    Main configuration (windows, groups, sensors) is stored in the
    Config Entry via Home Assistant's Config Flow system.
    This store only persists user overrides for thresholds and
    scenarios that are adjusted via dashboard entities.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the ConfigStore.

        Args:
            hass: The Home Assistant instance.
        """
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.version = STORAGE_VERSION

    async def async_load(self) -> dict:
        """Load overrides from storage.

        Returns:
            Dictionary with overrides. Returns empty overrides
            if no data has been saved yet.
        """
        data = await self._store.async_load()
        if data is None:
            return self._get_empty_overrides()
        return data

    async def async_save(self, overrides: dict) -> None:
        """Save overrides to storage.

        Args:
            overrides: Dictionary of overrides to save.
        """
        await self._store.async_save(overrides)

    def _get_empty_overrides(self) -> dict:
        """Return empty overrides structure.

        Returns:
            Dictionary with empty overrides structure.
        """
        return {
            "version": self.version,
            CONF_OVERRIDES: {},
        }
