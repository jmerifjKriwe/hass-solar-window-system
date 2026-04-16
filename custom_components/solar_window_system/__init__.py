"""Solar Window System integration for Home Assistant."""

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.storage import Store

from .const import (
    CONF_OVERRIDES,
    DOMAIN,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from .coordinator import SolarCalculationCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SWITCH,
    Platform.BUTTON,
    "diagnostic_sensor",
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Solar Window System from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}

    # Get config from entry data
    config = dict(entry.data)

    # Load overrides from storage (if any)
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    stored_data = await store.async_load() or {}
    overrides = stored_data.get(CONF_OVERRIDES, {})

    # Build subentries dict from entry.subentries (proper HA 2026.4+ API)
    subentries: dict[str, Any] = {}
    if hasattr(entry, "subentries"):
        for subentry_id, subentry in entry.subentries.items():
            subentries[subentry_id] = {
                **subentry.data,
                "type": subentry.subentry_type,
                "name": subentry.title,
            }

    # Check if coordinator already exists (reload scenario)
    existing_coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id, {}).get("coordinator")

    # Create coordinator with subentries and overrides
    coordinator = SolarCalculationCoordinator(hass, config, subentries, overrides, entry)
    coordinator.set_store(store)

    if existing_coordinator:
        # Reload: use regular refresh instead of first_refresh
        await coordinator.async_request_refresh()
    else:
        # First setup: use first_refresh
        await coordinator.async_config_entry_first_refresh()

    # Store coordinator and references
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator
    hass.data[DOMAIN][entry.entry_id]["config"] = config
    hass.data[DOMAIN][entry.entry_id]["store"] = store

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Run initial config validation
    coordinator.validate_configuration()

    # Listen for config entry updates (new subentries added)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_on_subentry_removed(
    hass: HomeAssistant, entry: ConfigEntry, subentry_id: str, subentry_type: str
) -> None:
    """Handle subentry removal - clean up entities and coordinator data.

    This function is called when a subentry (window or group) is removed.
    It cleans up the associated entities and removes the subentry from
    the coordinator's data structures.
    """
    _LOGGER.info("async_on_subentry_removed called for %s (type: %s)", subentry_id, subentry_type)

    # Get coordinator
    domain_data = hass.data.get(DOMAIN, {})
    entry_data = domain_data.get(entry.entry_id, {})
    coordinator = entry_data.get("coordinator")

    if not coordinator:
        _LOGGER.warning("No coordinator found for entry %s", entry.entry_id)
        return

    # Get registries
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)

    # Determine device_id and data structure based on subentry type
    if subentry_type == "group":
        device_id = f"group_{subentry_id}"
        unique_id_prefix = f"{DOMAIN}_group_{subentry_id}"
        # Remove from coordinator groups
        if subentry_id in coordinator.groups:
            del coordinator.groups[subentry_id]
            _LOGGER.debug("Removed group %s from coordinator", subentry_id)
    elif subentry_type == "window":
        device_id = f"window_{subentry_id}"
        unique_id_prefix = f"{DOMAIN}_window_{subentry_id}"
        # Remove from coordinator windows
        if subentry_id in coordinator.windows:
            del coordinator.windows[subentry_id]
            _LOGGER.debug("Removed window %s from coordinator", subentry_id)
    else:
        _LOGGER.warning("Unknown subentry type: %s", subentry_type)
        return

    # Remove entities for this subentry
    entities_to_remove = [
        entity.entity_id
        for entity in er.async_entries_for_config_entry(entity_registry, entry.entry_id)
        if entity.device_id is not None and entity.unique_id.startswith(unique_id_prefix)
    ]
    for entity_id in entities_to_remove:
        _LOGGER.debug("Removing entity: %s", entity_id)
        entity_registry.async_remove(entity_id)

    # Remove device
    device = device_registry.async_get_device(identifiers={(DOMAIN, device_id)})
    if device:
        _LOGGER.debug("Removing device: %s", device_id)
        device_registry.async_remove_device(device.id)


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle config entry updates - reload platforms when subentries change."""
    _LOGGER.info("Update listener called - reloading platforms for new subentries")

    # Get the existing coordinator
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id, {}).get("coordinator")

    if not coordinator:
        _LOGGER.warning("No coordinator found, skipping update")
        return

    # Store old subentry IDs before updating
    old_groups = set(coordinator.groups.keys())
    old_windows = set(coordinator.windows.keys())

    # Rebuild subentries from the updated entry
    subentries: dict[str, Any] = {}
    if hasattr(entry, "subentries"):
        for subentry_id, subentry in entry.subentries.items():
            subentries[subentry_id] = {
                **subentry.data,
                "type": subentry.subentry_type,
                "name": subentry.title,
            }

    # Update the coordinator with new subentries
    coordinator._subentries = subentries
    coordinator.windows = coordinator._extract_windows()
    coordinator.groups = coordinator._extract_groups()

    # Store new subentry IDs after updating
    new_groups = set(coordinator.groups.keys())
    new_windows = set(coordinator.windows.keys())

    _LOGGER.info(
        "Coordinator updated - windows=%d, groups=%d",
        len(coordinator.windows),
        len(coordinator.groups),
    )

    # Remove entities for deleted subentries
    removed_groups = old_groups - new_groups
    removed_windows = old_windows - new_windows

    if removed_groups or removed_windows:
        _LOGGER.info(
            "Removing entities for deleted subentries: groups=%s, windows=%s",
            removed_groups,
            removed_windows,
        )
        entity_registry = er.async_get(hass)
        device_registry = dr.async_get(hass)

        # Remove entities and devices for deleted groups
        for group_id in removed_groups:
            device_id = f"group_{group_id}"
            entities_to_remove = [
                entity.entity_id
                for entity in er.async_entries_for_config_entry(entity_registry, entry.entry_id)
                if entity.device_id is not None
                and entity.unique_id.startswith(f"{DOMAIN}_group_{group_id}")
            ]
            for entity_id in entities_to_remove:
                _LOGGER.debug("Removing entity: %s", entity_id)
                entity_registry.async_remove(entity_id)
            device = device_registry.async_get_device(identifiers={(DOMAIN, device_id)})
            if device:
                _LOGGER.debug("Removing device: %s", device_id)
                device_registry.async_remove_device(device.id)

        # Remove entities and devices for deleted windows
        for window_id in removed_windows:
            device_id = f"window_{window_id}"
            entities_to_remove = [
                entity.entity_id
                for entity in er.async_entries_for_config_entry(entity_registry, entry.entry_id)
                if entity.device_id is not None
                and entity.unique_id.startswith(f"{DOMAIN}_window_{window_id}")
            ]
            for entity_id in entities_to_remove:
                _LOGGER.debug("Removing entity: %s", entity_id)
                entity_registry.async_remove(entity_id)
            device = device_registry.async_get_device(identifiers={(DOMAIN, device_id)})
            if device:
                _LOGGER.debug("Removing device: %s", device_id)
                device_registry.async_remove_device(device.id)

    # Reload platforms: unload and setup again to create/remove entities
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry (for manual reload from UI)."""
    # Unload and reload the entry
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
