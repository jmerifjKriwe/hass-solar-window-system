# /config/custom_components/solar_window_system/__init__.py

import logging
import os
import yaml

from homeassistant.core import HomeAssistant, CoreState, ServiceCall
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
        # Only load groups and windows - defaults come from UI entities
        with open(os.path.join(config_path, "groups.yaml"), "r", encoding="utf-8") as f:
            groups_config = yaml.safe_load(f).get("groups", {})
        with open(
            os.path.join(config_path, "windows.yaml"), "r", encoding="utf-8"
        ) as f:
            windows_config = yaml.safe_load(f).get("windows", {})

        # Create built-in defaults that match the number.py default values
        defaults_config = {
            "physical": {
                "g_value": 0.5,
                "frame_width": 0.125,
                "diffuse_factor": 0.15,
                "tilt": 90,
            },
            "thresholds": {"direct": 200, "diffuse": 150},
            "temperatures": {"indoor_base": 23.0, "outdoor_base": 19.5},
            "scenario_b": {
                "enabled": True,
                "temp_indoor_offset": 0.5,
                "temp_outdoor_offset": 6.0,
            },
            "scenario_c": {
                "enabled": True,
                "temp_forecast_threshold": 28.5,
                "temp_indoor_threshold": 21.5,
                "temp_outdoor_threshold": 24.0,
                "start_hour": 9,
            },
            "calculation": {"min_solar_radiation": 50, "min_sun_elevation": 10},
        }

        return {
            "defaults": defaults_config,
            "groups": groups_config,
            "windows": windows_config,
        }
    except FileNotFoundError as e:
        raise ConfigEntryNotReady(
            f"Configuration file not found in {config_path}: {e}"
        ) from e


async def _setup_integration(
    hass: HomeAssistant, entry: ConfigEntry, is_delayed: bool = False
):
    """Contains the shared setup logic."""
    _LOGGER.info("Proceeding with setup for entry %s.", entry.entry_id)

    config_data = await hass.async_add_executor_job(_load_config_from_files, hass)

    coordinator = SolarWindowDataUpdateCoordinator(hass, entry, config_data)

    # Use async_config_entry_first_refresh to ensure data is available before entity setup
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register the service
    await _register_services(hass, coordinator)


async def _register_services(
    hass: HomeAssistant, coordinator: SolarWindowDataUpdateCoordinator
):
    """Register services for the integration."""
    # Check if service is already registered to avoid duplicates
    if not hass.services.has_service(DOMAIN, "update_now"):

        async def async_update_now_service(call: ServiceCall) -> None:
            """Service call to force an immediate data update."""
            _LOGGER.info(
                "Service solar_window_system.update_now called, requesting refresh."
            )
            await coordinator.async_request_refresh()

        hass.services.async_register(DOMAIN, "update_now", async_update_now_service)
        _LOGGER.info("Registered service solar_window_system.update_now")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Solar Window System from a config entry, waiting if necessary."""

    if hass.state is CoreState.running:
        await _setup_integration(hass, entry, is_delayed=False)
    else:
        _LOGGER.info("Home Assistant is not fully started yet. Deferring setup.")

        async def delayed_setup(event):
            """Handle the actual setup once Home Assistant is started."""
            _LOGGER.info("Starting delayed setup for entry %s", entry.entry_id)
            fresh_entry = hass.config_entries.async_get_entry(entry.entry_id)
            if fresh_entry:
                await _setup_integration(hass, fresh_entry, is_delayed=True)
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

    # Service wieder abmelden, wenn die Integration entladen wird
    # Aber nur, wenn es das letzte Entry ist
    if len(hass.config_entries.async_entries(DOMAIN)) <= 1:
        if hass.services.has_service(DOMAIN, "update_now"):
            hass.services.async_remove(DOMAIN, "update_now")
            _LOGGER.info("Unregistered service solar_window_system.update_now")

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
            hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle a reload request from the UI."""
    _LOGGER.info("Reloading Solar Window System integration.")
    await hass.config_entries.async_reload(entry.entry_id)
