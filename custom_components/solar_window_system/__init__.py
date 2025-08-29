"""Solar Window System integration package."""

from datetime import UTC, datetime
import json
import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .const import DOMAIN
from .coordinator import SolarWindowSystemCoordinator

_LOGGER = logging.getLogger(__name__)

# Minimum length for device identifier tuples (domain, identifier)
MIN_IDENT_TUPLE_LEN = 2


async def _resolve_to_subentry_id(hass: HomeAssistant, value: str) -> str:
    """
    Resolve a provided value to a subentry window id.

    Accepts raw subentry ids (returned unchanged), entity ids, or device ids.
    Resolves entity -> device -> device.identifiers and returns the
    subentry_id (without 'window_' prefix) for this domain.
    """
    if not value:
        return value

    # First, try to resolve as device id
    dev_reg = dr.async_get(hass)
    dev = dev_reg.async_get(value) if isinstance(value, str) else None
    if dev and dev.identifiers:
        # Found a device, extract window identifier
        for ident in dev.identifiers:
            if (
                isinstance(ident, tuple)
                and len(ident) >= MIN_IDENT_TUPLE_LEN
                and ident[0] == DOMAIN
            ):
                candidate = ident[1]
                if isinstance(candidate, str) and candidate.startswith("window_"):
                    # Return subentry_id without 'window_' prefix
                    return candidate[7:]

    # Second, try to resolve as entity id
    ent = None
    if isinstance(value, str) and "." in value:
        ent_reg = er.async_get(hass)
        ent = ent_reg.async_get(value)

    if ent and ent.device_id:
        # Found entity with device, resolve the device
        dev = dev_reg.async_get(ent.device_id)
        if dev and dev.identifiers:
            for ident in dev.identifiers:
                if (
                    isinstance(ident, tuple)
                    and len(ident) >= MIN_IDENT_TUPLE_LEN
                    and ident[0] == DOMAIN
                ):
                    candidate = ident[1]
                    if isinstance(candidate, str) and candidate.startswith("window_"):
                        # Return subentry_id without 'window_' prefix
                        return candidate[7:]

    # Third, if it already looks like a subentry id (no window_ prefix), return as-is
    if isinstance(value, str) and not value.startswith("window_"):
        return value

    # Fourth, if it starts with window_, extract the subentry_id
    if isinstance(value, str) and value.startswith("window_"):
        return value[7:]  # Remove 'window_' prefix

    # Fallback: return original value unchanged
    return value


def _get_integration_version() -> str:
    """Get the integration version from manifest.json."""
    try:
        manifest_path = Path(__file__).parent / "manifest.json"
        with manifest_path.open("r", encoding="utf-8") as f:
            manifest = json.load(f)
        return manifest.get("version", "unknown")
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        _LOGGER.warning("Could not read version from manifest.json")
        return "unknown"


def _register_services(hass: HomeAssistant) -> None:
    """Register all services for the Solar Window System integration."""
    # Register recalculate service (only once)
    if not hass.services.has_service(DOMAIN, "solar_window_system_recalculate"):

        async def handle_recalculate_service(call: ServiceCall) -> None:
            """Service to trigger recalculation for all or a specific window."""
            window_id = call.data.get("window_id")
            # Recalculate for all window_configs coordinators
            for config_entry in hass.config_entries.async_entries(DOMAIN):
                if config_entry.data.get("entry_type") == "window_configs":
                    coordinator = hass.data[DOMAIN][config_entry.entry_id][
                        "coordinator"
                    ]
                    await coordinator.async_refresh()
                    # If a specific window_id is given, optionally filter or log
                    if window_id:
                        _LOGGER.info(
                            "Recalculation triggered for window: %s", window_id
                        )
                    else:
                        _LOGGER.info("Recalculation triggered for all windows.")

        hass.services.async_register(
            DOMAIN, "solar_window_system_recalculate", handle_recalculate_service
        )

    # Register debug_calculation service (only once)
    if not hass.services.has_service(DOMAIN, "solar_window_system_debug_calculation"):

        async def handle_debug_calculation_service(call: ServiceCall) -> None:
            """Service to create debug calculation file for a window."""
            window_id = call.data.get("window_id")
            filename = call.data.get("filename")

            if not window_id:
                _LOGGER.error("Window ID is required for debug calculation")
                return

            # Resolve the window_id to a proper subentry id
            resolved_window_id = await _resolve_to_subentry_id(hass, window_id)

            # Find the coordinator for this window
            for config_entry in hass.config_entries.async_entries(DOMAIN):
                if config_entry.data.get("entry_type") == "window_configs":
                    coordinator = hass.data[DOMAIN][config_entry.entry_id][
                        "coordinator"
                    ]

                    # Create debug data
                    debug_data = await coordinator.create_debug_data(resolved_window_id)

                    if debug_data:
                        # Generate filename if not provided
                        if not filename:
                            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
                            filename = f"debug_{resolved_window_id}_{timestamp}.json"

                        # Save to config directory
                        config_dir = Path(hass.config.config_dir)
                        file_path = config_dir / filename

                        try:
                            with file_path.open("w", encoding="utf-8") as f:
                                json.dump(
                                    debug_data,
                                    f,
                                    indent=2,
                                    ensure_ascii=False,
                                    default=str,
                                )

                            _LOGGER.info("Debug file created: %s", file_path)

                            await hass.services.async_call(
                                "persistent_notification",
                                "create",
                                {
                                    "title": "Debug File Created",
                                    "message": (
                                        f"Debug calculation file saved to: {filename}"
                                    ),
                                },
                            )

                        except OSError:
                            _LOGGER.exception("Failed to create debug file")

                    else:
                        _LOGGER.error(
                            "Could not create debug data for window: %s",
                            resolved_window_id,
                        )

        hass.services.async_register(
            DOMAIN,
            "solar_window_system_debug_calculation",
            handle_debug_calculation_service,
        )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the Solar Window System integration from a config entry."""
    # Register services once
    _register_services(hass)

    update_interval_minutes = 1
    for config_entry in hass.config_entries.async_entries(DOMAIN):
        if config_entry.data.get("entry_type") == "global_config":
            update_interval_minutes = config_entry.options.get(
                "update_interval", config_entry.data.get("update_interval", 1)
            )
            break

    _LOGGER.debug("Setting up entry: %s", entry.title)
    _LOGGER.debug("Entry data: %s", entry.data)
    _LOGGER.debug("Entry ID: %s", entry.entry_id)

    device_registry = dr.async_get(hass)

    # Create device for global config
    if entry.title == "Solar Window System":
        _LOGGER.debug("Creating device for global config")
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, "global_config")},
            name="Solar Window System",
            manufacturer="SolarWindowSystem",
            model="GlobalConfig",
            sw_version=_get_integration_version(),
        )

        # Set up all platforms for this entry
        await hass.config_entries.async_forward_entry_setups(
            entry, ["sensor", "number", "text", "select", "switch"]
        )

    # Handle group configurations entry (subentry parent)
    elif entry.data.get("entry_type") == "group_configs":
        # Create devices for existing subentries
        await _create_subentry_devices(hass, entry)

        # Initialize coordinator for group configurations as well
        coordinator = SolarWindowSystemCoordinator(hass, entry, update_interval_minutes)

        # Store coordinator per entry to support multiple entries
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

        # Start coordinator updates
        await coordinator.async_config_entry_first_refresh()

        # Set up platforms for group configurations
        await hass.config_entries.async_forward_entry_setups(
            entry, ["select", "sensor"]
        )

        # Add update listener to handle new subentries
        entry.add_update_listener(_handle_config_entry_update)

    # Handle window configurations entry (subentry parent)
    elif entry.data.get("entry_type") == "window_configs":
        # Create devices for existing subentries
        await _create_subentry_devices(hass, entry)

        # Initialize coordinator for calculation updates
        coordinator = SolarWindowSystemCoordinator(hass, entry, update_interval_minutes)

        # Store coordinator in hass.data for access by binary sensors
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

        # Start coordinator updates
        await coordinator.async_config_entry_first_refresh()

        # Set up platforms for window configurations
        await hass.config_entries.async_forward_entry_setups(
            entry, ["select", "sensor", "binary_sensor", "number", "text", "switch"]
        )

        # Add update listener to handle new subentries
        entry.add_update_listener(_handle_config_entry_update)

    # Register service for manual device creation (only once)
    if not hass.services.has_service(DOMAIN, "create_subentry_devices"):

        async def create_subentry_devices_service(
            _call: ServiceCall,
        ) -> None:
            """Service to manually create subentry devices."""
            for config_entry in hass.config_entries.async_entries(DOMAIN):
                if config_entry.data.get("entry_type") in [
                    "group_configs",
                    "window_configs",
                ]:
                    await _create_subentry_devices(hass, config_entry)

        hass.services.async_register(
            DOMAIN, "create_subentry_devices", create_subentry_devices_service
        )

    _LOGGER.debug("Setup completed for: %s", entry.title)
    return True


async def _handle_debug_calculation_service(
    hass: HomeAssistant, call: ServiceCall
) -> None:
    """Service to create debug calculation file for a window."""
    window_id = call.data.get("window_id")
    filename = call.data.get("filename")

    if not window_id:
        _LOGGER.error("Window ID is required for debug calculation")
        return

    # Resolve the window_id to a proper subentry id
    resolved_window_id = await _resolve_to_subentry_id(hass, window_id)

    # Find the coordinator for this window
    for config_entry in hass.config_entries.async_entries(DOMAIN):
        if config_entry.data.get("entry_type") == "window_configs":
            coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

            # Create debug data
            debug_data = await coordinator.create_debug_data(resolved_window_id)

            if debug_data:
                # Generate filename if not provided
                if not filename:
                    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
                    filename = f"debug_{resolved_window_id}_{timestamp}.json"

                # Save to config directory
                config_dir = Path(hass.config.config_dir)
                file_path = config_dir / filename

                try:
                    with file_path.open("w", encoding="utf-8") as f:
                        json.dump(
                            debug_data, f, indent=2, ensure_ascii=False, default=str
                        )

                    _LOGGER.info("Debug file created: %s", file_path)

                    # Optional: Create a persistent notification
                    await hass.services.async_call(
                        "persistent_notification",
                        "create",
                        {
                            "title": "Debug File Created",
                            "message": f"Debug calculation file saved to: {filename}",
                        },
                    )

                except OSError:
                    _LOGGER.exception("Failed to create debug file")
            else:
                _LOGGER.error(
                    "Could not create debug data for window: %s", resolved_window_id
                )


@callback
async def _handle_config_entry_update(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle config entry updates to create devices for new subentries."""
    _LOGGER.debug("Config entry update detected for: %s", entry.title)
    if entry.data.get("entry_type") in ["group_configs", "window_configs"]:
        await _create_subentry_devices(hass, entry)

        # Reconfigure coordinator if this entry manages flows
        if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
            coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
            await coordinator.async_reconfigure()

        # Reload select platform to pick up new entities for new subentries
        _LOGGER.debug("Reloading platforms for updated entry: %s", entry.title)
        if entry.data.get("entry_type") in ("group_configs", "window_configs"):
            # Reload platforms to pick up entities for new subentries
            platforms = ["select", "sensor"]
            if entry.data.get("entry_type") == "window_configs":
                platforms.append("binary_sensor")
            await hass.config_entries.async_unload_platforms(entry, platforms)
            await hass.config_entries.async_forward_entry_setups(entry, platforms)


async def _create_subentry_devices(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Create devices for all subentries using proper Device Registry API."""
    device_registry = dr.async_get(hass)

    # The correct way to access subentries is through entry.subentries
    # This is a dict where keys are subentry IDs and values are ConfigSubentry objects

    if getattr(entry, "subentries", None):
        for subentry_id, subentry in entry.subentries.items():
            if subentry.subentry_type == "group":
                group_name = subentry.title
                _LOGGER.debug("Creating device for group subentry: %s", group_name)

                # This is the key: use config_subentry_id parameter
                # to link device to subentry
                device = device_registry.async_get_or_create(
                    config_entry_id=entry.entry_id,
                    config_subentry_id=subentry_id,  # Links device to subentry!
                    identifiers={(DOMAIN, f"group_{subentry_id}")},
                    name=group_name,
                    manufacturer="SolarWindowSystem",
                    model="GroupConfig",
                )
                _LOGGER.debug(
                    "Device created for subentry: %s (%s)", device.name, device.id
                )
            elif subentry.subentry_type == "window":
                window_name = subentry.title
                _LOGGER.debug("Creating device for window subentry: %s", window_name)

                # Create device for window subentry
                device = device_registry.async_get_or_create(
                    config_entry_id=entry.entry_id,
                    config_subentry_id=subentry_id,  # Links device to subentry!
                    identifiers={(DOMAIN, f"window_{subentry_id}")},
                    name=window_name,
                    manufacturer="SolarWindowSystem",
                    model="WindowConfig",
                )
                _LOGGER.debug(
                    "Device created for subentry: %s (%s)", device.name, device.id
                )
                _LOGGER.debug(
                    "Device config_entries_subentries: %s",
                    device.config_entries_subentries,
                )
            else:
                _LOGGER.debug(
                    "Skipping subentry (unknown type): %s", subentry.subentry_type
                )
    else:
        _LOGGER.debug("No subentries found in entry")


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading entry: %s", entry.title)

    # Unload platforms if this is the global config entry
    if entry.title == "Solar Window System":
        return await hass.config_entries.async_unload_platforms(
            entry, ["sensor", "number", "text", "select", "switch"]
        )

    # Handle window_configs entry unloading
    if entry.data.get("entry_type") == "window_configs":
        # Clean up coordinator
        if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
            del hass.data[DOMAIN][entry.entry_id]

        return await hass.config_entries.async_unload_platforms(
            entry, ["select", "sensor", "binary_sensor"]
        )

    # Handle group_configs entry unloading
    if entry.data.get("entry_type") == "group_configs":
        # Clean up coordinator
        if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
            del hass.data[DOMAIN][entry.entry_id]
        return await hass.config_entries.async_unload_platforms(
            entry, ["select", "sensor"]
        )

    return True
