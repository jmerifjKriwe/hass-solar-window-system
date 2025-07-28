from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import logging

_LOGGER = logging.getLogger(__name__)
DOMAIN = "solar_window_system"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.info("Running async_setup_entry")
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"dummy": True}
    return True
