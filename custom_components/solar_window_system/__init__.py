"""Solar Window System Home Assistant integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.device_registry import async_get as async_get_device_registry

from .const import CONF_ENTRY_TYPE, CONF_WINDOW_NAME, DOMAIN, PLATFORMS
from .coordinator import SolarWindowDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Solar Window System from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    entry_type = entry.data.get(CONF_ENTRY_TYPE)

    if entry_type == "global":
        config_data = entry.options
        if not config_data:
            _LOGGER.info(
                "No configuration provided yet. Integration will be idle until configured."
            )

        coordinator = SolarWindowDataUpdateCoordinator(hass, entry, config_data)
        hass.data[DOMAIN][entry.entry_id] = coordinator

        # The original code had this commented out. I'll respect that.
        # await coordinator.async_config_entry_first_refresh()

        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        entry.async_on_unload(entry.add_update_listener(options_update_listener))

        if not hass.services.has_service(DOMAIN, "update_now"):
            _LOGGER.info("Registering service solar_window_system.update_now")

            async def handle_update_now(_: ServiceCall) -> None:
                """Handle the service call."""
                _LOGGER.info("Service 'update_now' called. Forcing data refresh.")
                await coordinator.async_request_refresh()

            hass.services.async_register(DOMAIN, "update_now", handle_update_now)

    elif entry_type == "window":
        device_registry = async_get_device_registry(hass)
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.data.get(CONF_WINDOW_NAME, "Unnamed Window"),
            model="Virtual Window",
            manufacturer="Example GmbH",
        )
        _LOGGER.info("Window entry %s registered as a device.", entry.entry_id)

    elif entry_type == "group":
        _LOGGER.info("Group entry %s setup (no specific actions yet).", entry.entry_id)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading entry %s", entry.entry_id)

    if entry.data.get(CONF_ENTRY_TYPE) != "global":
        return True

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
            if hass.services.has_service(DOMAIN, "update_now"):
                hass.services.async_remove(DOMAIN, "update_now")
    return unload_ok


async def options_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.debug("Configuration options updated, reloading integration.")
    await hass.config_entries.async_reload(entry.entry_id)
