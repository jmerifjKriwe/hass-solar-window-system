"""Solar Window System Home Assistant integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import CoreState, HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, PLATFORMS
from .coordinator import SolarWindowDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)





async def _setup_integration(
    hass: HomeAssistant, entry: ConfigEntry, *, delayed: bool
) -> None:
    _LOGGER.info(
        "Proceeding with setup for entry %s (delayed: %s)", entry.entry_id, delayed
    )
    config_data = entry.options

    if not config_data:
        _LOGGER.info(
            "No configuration provided yet. Integration will be idle until configured."
        )
        # Continue to set up coordinator and platforms to allow UI configuration
        # No platforms will be loaded if config_data is empty, as they rely on it.

    coordinator = SolarWindowDataUpdateCoordinator(hass, entry, config_data)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # await coordinator.async_config_entry_first_refresh() # Temporarily disabled to prevent immediate calculations

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    hass.data[DOMAIN]["loaded_platforms"] = set(PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    if not hass.services.has_service(DOMAIN, "update_now"):
        _LOGGER.info("Registering service solar_window_system.update_now")

        async def handle_update_now(_: ServiceCall) -> None:
            """Handle the service call."""
            _LOGGER.info("Service 'update_now' called. Forcing data refresh.")
            await coordinator.async_request_refresh()

        hass.services.async_register(DOMAIN, "update_now", handle_update_now)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Solar Window System from a config entry."""
    if hass.state is CoreState.running:
        await _setup_integration(hass, entry, delayed=False)
    else:
        _LOGGER.info("Home Assistant not started yet, delaying setup.")

        async def delayed_setup(_: object) -> None:
            _LOGGER.info("Delayed setup started after Home Assistant start event")
            fresh_entry = hass.config_entries.async_get_entry(entry.entry_id)
            if fresh_entry:
                await _setup_integration(hass, fresh_entry, delayed=True)
            else:
                _LOGGER.error(
                    "Could not find config entry %s during delayed setup",
                    entry.entry_id,
                )

        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, delayed_setup)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading entry %s", entry.entry_id)

    domain_data = hass.data.get(DOMAIN)
    if not domain_data:
        return True  # Nothing to unload

    loaded_platforms = domain_data.get("loaded_platforms", set())
    _LOGGER.info("Platforms to unload: %s", loaded_platforms)

    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, list(loaded_platforms)
    )

    if unload_ok:
        domain_data.pop(entry.entry_id, None)
        domain_data.pop("loaded_platforms", None)
        if not domain_data:
            hass.data.pop(DOMAIN)

    if not hass.config_entries.async_entries(DOMAIN) and hass.services.has_service(
        DOMAIN, "update_now"
    ):
        hass.services.async_remove(DOMAIN, "update_now")
        _LOGGER.info("Unregistered service solar_window_system.update_now")

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle a reload request from the UI."""
    _LOGGER.info("Reloading Solar Window System integration.")
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)