"""Solar Window System Home Assistant integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import CoreState, HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, PLATFORMS
from .coordinator import SolarWindowDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


def _get_default_config() -> dict:
    """Return the built-in default configuration matching number entities."""
    return {
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
            "start_hour": 9,
        },
        "calculation": {"min_sun_elevation": 10},
    }


async def _load_config_from_subentries(hass: HomeAssistant, entry: ConfigEntry) -> dict:
    """Load Defaults, Groups, and Windows config from sub-entries."""
    # Home Assistant 2025.7.4+ sub-entry API
    # Use async_children if available, else filter async_entries by parent_entry_id
    sub_entries = []
    # Only use fallback, as async_children is not always present
    sub_entries = [
        e
        for e in hass.config_entries.async_entries(DOMAIN)
        if getattr(e, "parent_entry_id", None) == entry.entry_id
    ]

    defaults_config = None
    groups_config = {}
    windows_config = {}

    for sub in sub_entries:
        # Identify by title or a type field in data
        if sub.title.lower() == "defaults":
            defaults_config = dict(sub.data)
        elif sub.title.lower().startswith("group") or sub.data.get("type") == "group":
            group_name = sub.data.get("name") or sub.title
            groups_config[group_name] = dict(sub.data)
        elif sub.title.lower().startswith("window") or sub.data.get("type") == "window":
            window_name = sub.data.get("name") or sub.title
            windows_config[window_name] = dict(sub.data)

    if defaults_config is None:
        defaults_config = _get_default_config()

    return {
        "defaults": defaults_config,
        "groups": groups_config,
        "windows": windows_config,
    }


async def _setup_integration(
    hass: HomeAssistant, entry: ConfigEntry, *, delayed: bool
) -> None:
    _LOGGER.info(
        "Proceeding with setup for entry %s (delayed: %s)", entry.entry_id, delayed
    )
    config_data = await _load_config_from_subentries(hass, entry)

    if not config_data.get("windows"):
        _LOGGER.info(
            "No windows configured in sub-entries. Integration will remain idle until at least one window is added. No platforms will be loaded."
        )
        # Do not set up coordinator or platforms, just return
        return

    coordinator = SolarWindowDataUpdateCoordinator(hass, entry, config_data)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await coordinator.async_config_entry_first_refresh()

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
