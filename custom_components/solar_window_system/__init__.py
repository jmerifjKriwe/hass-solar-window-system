"""Solar Window System integration package."""

from __future__ import annotations

# Standard library
import asyncio
from datetime import UTC, datetime
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

# Third-party / Home Assistant
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import CoreState, HomeAssistant, ServiceCall, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

# Local
from .const import DOMAIN
from .coordinator import SolarWindowSystemCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry


_LOGGER = logging.getLogger(__name__)

# Minimum length for device identifier tuples (domain, identifier)
MIN_IDENT_TUPLE_LEN = 2


def _write_debug_file(file_path: Path, debug_data: dict) -> None:
    """Write debug data to file (blocking operation for thread executor)."""
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(
            debug_data,
            f,
            indent=2,
            ensure_ascii=False,
            default=str,
        )


async def _resolve_to_subentry_id(hass: HomeAssistant, value: str) -> str:
    """
    Resolve a provided value to a subentry window id.

    Accepts raw subentry ids (returned unchanged), entity ids, or device ids.
    Resolves entity -> device -> device.identifiers and returns the
    subentry_id (without 'window_' prefix) for this domain.
    """
    if not value:
        return value

    # Handle direct subentry id cases first
    if isinstance(value, str):
        if not value.startswith("window_"):
            return value
        return value[7:]  # Remove 'window_' prefix

    # Try to resolve as device id or entity id
    dev_reg = dr.async_get(hass)
    subentry_id = await _extract_subentry_from_device(dev_reg, value)
    if subentry_id:
        return subentry_id

    # Try to resolve as entity id
    if isinstance(value, str) and "." in value:
        ent_reg = er.async_get(hass)
        ent = ent_reg.async_get(value)
        if ent and ent.device_id:
            subentry_id = await _extract_subentry_from_device(dev_reg, ent.device_id)
            if subentry_id:
                return subentry_id

    return value


async def _extract_subentry_from_device(
    dev_reg: dr.DeviceRegistry, device_id: str
) -> str | None:
    """Extract subentry id from device identifiers."""
    dev = dev_reg.devices.get(device_id)
    if not dev or not dev.identifiers:
        return None

    for ident in dev.identifiers:
        if (
            isinstance(ident, tuple)
            and len(ident) >= MIN_IDENT_TUPLE_LEN
            and ident[0] == DOMAIN
        ):
            candidate = ident[1]
            if isinstance(candidate, str) and candidate.startswith("window_"):
                return candidate[7:]  # Remove 'window_' prefix

    return None


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


async def _async_get_integration_version(hass: HomeAssistant) -> str:
    """Get the integration version from manifest.json (async version)."""
    # Check if version is already cached
    if DOMAIN in hass.data and "integration_version" in hass.data[DOMAIN]:
        return hass.data[DOMAIN]["integration_version"]

    # Read version from manifest.json using thread pool to avoid blocking
    def _read_version() -> str:
        try:
            manifest_path = Path(__file__).parent / "manifest.json"
            with manifest_path.open("r", encoding="utf-8") as f:
                manifest = json.load(f)
            return manifest.get("version", "unknown")
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            _LOGGER.warning("Could not read version from manifest.json")
            return "unknown"

    # Run the blocking I/O in a thread pool
    loop = asyncio.get_event_loop()
    version = await loop.run_in_executor(None, _read_version)

    # Cache the version
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["integration_version"] = version

    return version


def _register_create_subentry_devices_service(hass: HomeAssistant) -> None:
    """
    Register the create_subentry_devices service if not already present.

    Extracted to reduce complexity inside async_setup_entry and make the
    logic easier to test.
    """
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
                            # Write debug data to file using thread executor
                            # to avoid blocking the event loop
                            loop = asyncio.get_event_loop()
                            await loop.run_in_executor(
                                None, _write_debug_file, file_path, debug_data
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

    async def _finish_setup_entry() -> None:
        """
        Finish setup once Home Assistant is running.

        This performs the device creation, coordinator setup and platform
        forwarding that can be noisy or fail if other integrations/entities
        are not yet available during core startup.
        """
        device_registry = dr.async_get(hass)

        # Create device for global config
        if entry.title == "Solar Window System":
            _LOGGER.debug("Creating device for global config")
            version = await _async_get_integration_version(hass)
            device_registry.async_get_or_create(
                config_entry_id=entry.entry_id,
                identifiers={(DOMAIN, "global_config")},
                name="Solar Window System",
                manufacturer="SolarWindowSystem",
                model="GlobalConfig",
                sw_version=version,
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
            coordinator = SolarWindowSystemCoordinator(
                hass, entry, update_interval_minutes
            )

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
            coordinator = SolarWindowSystemCoordinator(
                hass, entry, update_interval_minutes
            )

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

        _LOGGER.debug("Deferred setup completed for: %s", entry.title)

    # If core is already running, finish setup immediately. Otherwise, wait
    # until Home Assistant has emitted the started event to avoid noisy logs
    # and race conditions with other integrations (MQTT, sensors, etc.).
    # Some test harnesses provide a mock HomeAssistant without a `state`
    # attribute. Use getattr to avoid AttributeError during tests.
    if getattr(hass, "state", None) == CoreState.running:
        await _finish_setup_entry()
    else:
        _LOGGER.debug(
            "Home Assistant not yet running, deferring heavy setup for: %s",
            entry.title,
        )

        # Some test environments provide a Mock HomeAssistant without a
        # `bus` or `async_create_background_task`. In those cases run the
        # deferred setup immediately to allow tests to exercise the result.
        bus = getattr(hass, "bus", None)
        if bus is None or not hasattr(bus, "async_listen_once"):
            _LOGGER.debug(
                "Event bus not available, running deferred setup immediately for: %s",
                entry.title,
            )
            await _finish_setup_entry()
        else:
            def _on_started(event: object) -> None:
                """
                Start deferred setup when Home Assistant has started.

                The event argument is required by the bus listener API. It is
                intentionally unused here.
                """
                # Mark event as intentionally unused for linters
                _ = event

                # Schedule coroutine (do not await here). Provide a name for typing
                # compatibility with typed Home Assistant helpers.
                hass.async_create_background_task(
                    _finish_setup_entry(), name=f"{DOMAIN}_deferred_setup"
                )

            hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _on_started)

    # Register service for manual device creation (only once)
    _register_create_subentry_devices_service(hass)

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
                    # Write debug data to file using thread executor
                    # to avoid blocking the event loop
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        None, _write_debug_file, file_path, debug_data
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
