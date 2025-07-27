# /config/custom_components/solar_window_system/__init__.py

import logging
import os
import yaml

from homeassistant.core import HomeAssistant, CoreState
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED

from .const import DOMAIN, PLATFORMS
from .coordinator import SolarWindowDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


def _load_config_from_files(hass: HomeAssistant) -> dict:
    """Load configuration from YAML files in a separate thread."""
    config_path = hass.config.path("solar_windows")
    try:
        with open(
            os.path.join(config_path, "defaults.yaml"), "r", encoding="utf-8"
        ) as f:
            defaults_config = yaml.safe_load(f).get("defaults", {})
        with open(os.path.join(config_path, "groups.yaml"), "r", encoding="utf-8") as f:
            groups_config = yaml.safe_load(f).get("groups", {})
        with open(
            os.path.join(config_path, "windows.yaml"), "r", encoding="utf-8"
        ) as f:
            windows_config = yaml.safe_load(f).get("windows", {})
        return {
            "defaults": defaults_config,
            "groups": groups_config,
            "windows": windows_config,
        }
    except FileNotFoundError as e:
        raise ConfigEntryNotReady(
            f"Configuration file not found in {config_path}"
        ) from e


async def _setup_integration(hass: HomeAssistant, entry: ConfigEntry):
    """Contains the shared setup logic."""
    _LOGGER.info("Proceeding with setup for entry %s.", entry.entry_id)

    config_data = await hass.async_add_executor_job(_load_config_from_files, hass)

    coordinator = SolarWindowDataUpdateCoordinator(hass, entry, config_data)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Solar Window System from a config entry, waiting if necessary."""

    if hass.state is CoreState.running:
        await _setup_integration(hass, entry)
    else:
        _LOGGER.info("Home Assistant is not fully started yet. Deferring setup.")

        async def delayed_setup(event):
            """Handle the actual setup once Home Assistant is started."""
            _LOGGER.info("Starting delayed setup for entry %s", entry.entry_id)
            # Get a fresh copy of the config entry to avoid stale data
            fresh_entry = hass.config_entries.async_get_entry(entry.entry_id)
            if fresh_entry:
                await _setup_integration(hass, fresh_entry)
            else:
                _LOGGER.error(
                    "Could not find config entry %s during delayed setup",
                    entry.entry_id,
                )

        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, delayed_setup)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Solar Window System integration.")
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
            hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle a reload request from the UI."""
    _LOGGER.info("Reloading Solar Window System integration.")
    await hass.config_entries.async_reload(entry.entry_id)
