# /config/custom_components/solar_window_system/utils.py

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant


async def update_config_option(
    hass: HomeAssistant, entry: ConfigEntry, key: str, value
) -> None:
    """Aktualisiere eine einzelne Option im ConfigEntry und löse eine Neuberechnung aus."""
    options = dict(entry.options)
    if options.get(key) == value:
        # Wert ist schon gesetzt, kein Update nötig
        return
    options[key] = value
    hass.config_entries.async_update_entry(entry, options=options)
