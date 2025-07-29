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


def _load_config_from_files(hass: HomeAssistant) -> dict:
    """Load window and group configuration from YAML files."""
    config_path = hass.config.path("solar_windows")

    _LOGGER.info(f"Looking for config files in: {config_path}")

    groups_config = {}
    windows_config = {}

    try:
        with open(os.path.join(config_path, "groups.yaml"), "r", encoding="utf-8") as f:
            groups_config = yaml.safe_load(f).get("groups", {})
            _LOGGER.info(
                f"groups.yaml loaded successfully with groups: {list(groups_config.keys())}"
            )
    except FileNotFoundError:
        _LOGGER.debug("groups.yaml not found, using empty configuration.")
    except Exception as e:
        _LOGGER.error("Error loading groups.yaml: %s", e)

    try:
        with open(
            os.path.join(config_path, "windows.yaml"), "r", encoding="utf-8"
        ) as f:
            windows_config = yaml.safe_load(f).get("windows", {})
            _LOGGER.info(
                f"windows.yaml loaded successfully with windows: {list(windows_config.keys())}"
            )
    except FileNotFoundError:
        _LOGGER.warning("windows.yaml not found. No windows will be configured.")
    except Exception as e:
        _LOGGER.error("Error loading windows.yaml: %s", e)

    return {"groups": groups_config, "windows": windows_config}


async def _setup_integration(hass: HomeAssistant, entry: ConfigEntry, is_delayed: bool):
    _LOGGER.info(
        f"Proceeding with setup for entry {entry.entry_id} (delayed: {is_delayed})"
    )
    file_config = await hass.async_add_executor_job(_load_config_from_files, hass)

    if not file_config.get("windows"):
        _LOGGER.error(
            f"No windows configured, aborting setup. File config: {file_config}"
        )
        raise ConfigEntryNotReady("No windows configured in windows.yaml")

    # 2. Get built-in defaults and combine into the final config object
    config_data = {
        "defaults": _get_default_config(),
        "groups": file_config.get("groups", {}),
        "windows": file_config.get("windows", {}),
    }

    # 3. Create and store the coordinator
    coordinator = SolarWindowDataUpdateCoordinator(hass, entry, config_data)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # 3. Create and store the coordinator
    coordinator = SolarWindowDataUpdateCoordinator(hass, entry, config_data)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # 4. Initial data refresh
    await coordinator.async_config_entry_first_refresh()

    # 5. Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    hass.data[DOMAIN]["loaded_platforms"] = set(PLATFORMS)

    # 6. Set up listeners and services
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    if not hass.services.has_service(DOMAIN, "update_now"):
        _LOGGER.info("Registering service solar_window_system.update_now")

        async def handle_update_now(call: ServiceCall):
            """Handle the service call."""
            _LOGGER.info("Service 'update_now' called. Forcing data refresh.")
            await coordinator.async_request_refresh()

        hass.services.async_register(DOMAIN, "update_now", handle_update_now)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Solar Window System from a config entry."""
    if hass.state is CoreState.running:
        await _setup_integration(hass, entry, is_delayed=False)
    else:
        _LOGGER.info("Home Assistant not started yet, delaying setup.")

        async def delayed_setup(event):
            _LOGGER.info("Delayed setup started after Home Assistant start event")
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
    _LOGGER.info(f"Unloading entry {entry.entry_id}")

    domain_data = hass.data.get(DOMAIN)
    if not domain_data:
        return True  # Nothing to unload

    loaded_platforms = domain_data.get("loaded_platforms", set())
    _LOGGER.info(f"Platforms to unload: {loaded_platforms}")

    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, list(loaded_platforms)
    )

    if unload_ok:
        domain_data.pop(entry.entry_id, None)
        domain_data.pop("loaded_platforms", None)
        if not domain_data:
            hass.data.pop(DOMAIN)

    if not hass.config_entries.async_entries(DOMAIN):
        if hass.services.has_service(DOMAIN, "update_now"):
            hass.services.async_remove(DOMAIN, "update_now")
            _LOGGER.info("Unregistered service solar_window_system.update_now")

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle a reload request from the UI."""
    _LOGGER.info("Reloading Solar Window System integration.")
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
