"""Solar Window System integration package."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Solar Window System from a config entry."""
    _LOGGER.warning("🔧 async_setup_entry called for entry: %s", entry.title)
    _LOGGER.warning("🔧 Entry data: %s", entry.data)
    _LOGGER.warning("🔧 Entry ID: %s", entry.entry_id)

    device_registry = dr.async_get(hass)

    # Create device for global config
    if entry.title == "Solar Window System":
        _LOGGER.warning("🔧 Creating device for global config")
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, "global_config")},
            name="SWS Global",
            manufacturer="SolarWindowSystem",
            model="GlobalConfig",
        )

        # Set up all platforms for this entry
        await hass.config_entries.async_forward_entry_setups(
            entry, ["sensor", "number", "text", "select", "switch"]
        )

    # Handle group configurations entry (subentry parent)
    elif entry.data.get("entry_type") == "group_configs":
        _LOGGER.warning(
            "🔧 Handling group_configs entry - this is the parent for subentries"
        )

        # Create devices for existing subentries
        await _create_subentry_devices(hass, entry)

        # Add update listener to handle new subentries
        entry.add_update_listener(_handle_config_entry_update)

        # Register service for manual device creation
        if not hass.services.has_service(DOMAIN, "create_subentry_devices"):

            async def create_subentry_devices_service(
                _call: ServiceCall,
            ) -> None:
                """Service to manually create subentry devices."""
                _LOGGER.warning("🔧 Manual service called: create_subentry_devices")
                for config_entry in hass.config_entries.async_entries(DOMAIN):
                    if config_entry.data.get("entry_type") in [
                        "group_configs",
                        "window_configs",
                    ]:
                        await _create_subentry_devices(hass, config_entry)

            hass.services.async_register(
                DOMAIN, "create_subentry_devices", create_subentry_devices_service
            )

    # Handle window configurations entry (subentry parent)
    elif entry.data.get("entry_type") == "window_configs":
        _LOGGER.warning(
            "🔧 Handling window_configs entry - this is the parent for subentries"
        )

        # Create devices for existing subentries
        await _create_subentry_devices(hass, entry)

        # Add update listener to handle new subentries
        entry.add_update_listener(_handle_config_entry_update)

    _LOGGER.warning("🔧 async_setup_entry completed for: %s", entry.title)
    return True


@callback
async def _handle_config_entry_update(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle config entry updates to create devices for new subentries."""
    _LOGGER.warning("🔧 Config entry update detected for: %s", entry.title)
    if entry.data.get("entry_type") in ["group_configs", "window_configs"]:
        await _create_subentry_devices(hass, entry)


async def _create_subentry_devices(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Create devices for all subentries using proper Device Registry API."""
    _LOGGER.warning("🔧 _create_subentry_devices called for entry: %s", entry.title)
    device_registry = dr.async_get(hass)

    # The correct way to access subentries is through entry.subentries
    # This is a dict where keys are subentry IDs and values are ConfigSubentry objects
    _LOGGER.warning("🔧 Entry subentries: %s", entry.subentries)
    _LOGGER.warning("🔧 Subentries type: %s", type(entry.subentries))

    if entry.subentries:
        for subentry_id, subentry in entry.subentries.items():
            _LOGGER.warning("🔧 Processing subentry ID: %s", subentry_id)
            _LOGGER.warning("🔧 Subentry object: %s", subentry)
            _LOGGER.warning("🔧 Subentry title: %s", subentry.title)
            _LOGGER.warning("🔧 Subentry data: %s", subentry.data)
            _LOGGER.warning("🔧 Subentry type: %s", subentry.subentry_type)

            if subentry.subentry_type == "group":
                group_name = subentry.title
                _LOGGER.warning("🔧 Creating device for group subentry: %s", group_name)

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
                _LOGGER.warning(
                    "🔧 Device created for subentry: %s (%s)",
                    device.name,
                    device.id,
                )
                _LOGGER.warning(
                    "🔧 Device config_entries_subentries: %s",
                    device.config_entries_subentries,
                )
            elif subentry.subentry_type == "window":
                window_name = subentry.title
                _LOGGER.warning(
                    "🔧 Creating device for window subentry: %s", window_name
                )

                # Create device for window subentry
                device = device_registry.async_get_or_create(
                    config_entry_id=entry.entry_id,
                    config_subentry_id=subentry_id,  # Links device to subentry!
                    identifiers={(DOMAIN, f"window_{subentry_id}")},
                    name=window_name,
                    manufacturer="SolarWindowSystem",
                    model="WindowConfig",
                )
                _LOGGER.warning(
                    "🔧 Device created for subentry: %s (%s)",
                    device.name,
                    device.id,
                )
                _LOGGER.warning(
                    "🔧 Device config_entries_subentries: %s",
                    device.config_entries_subentries,
                )
            else:
                _LOGGER.warning(
                    "🔧 Skipping subentry (unknown type): %s",
                    subentry.subentry_type,
                )
    else:
        _LOGGER.warning("🔧 No subentries found in entry")


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.warning("🔧 async_unload_entry called for: %s", entry.title)

    # Unload platforms if this is the global config entry
    if entry.title == "Solar Window System":
        return await hass.config_entries.async_unload_platforms(
            entry, ["sensor", "number", "text", "select", "switch"]
        )

    return True
