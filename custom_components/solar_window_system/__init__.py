"""Solar Window System integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.helpers import device_registry as dr

from .const import (
    CONF_WINDOW,
    CONF_WINDOW_NAME,
    DOMAIN,
    ENTRY_TYPE_MAIN,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

PLATFORMS = []  # Will be populated in the future as more functionality is added


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Solar Window System from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Store config entry data in hass.data
    hass.data[DOMAIN][entry.entry_id] = entry.data

    entry_type = entry.data.get("entry_type")

    if entry_type == ENTRY_TYPE_MAIN:
        # This is the main Solar Window System entry
        return await async_setup_main_entry(hass, entry)
    elif entry_type == "window_configuration":
        # This is the Window Configuration entry
        return await async_setup_window_config_entry(hass, entry)
    elif CONF_WINDOW_NAME in entry.data and CONF_WINDOW in entry.data:
        # This is a window sub-entry
        return await async_setup_window_entry(hass, entry)

    # Fallback for legacy entries without entry_type
    _LOGGER.warning("Unknown entry type for %s", entry.title)
    return True


async def async_setup_main_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the main Solar Window System entry."""
    device_registry = dr.async_get(hass)

    # Create main Solar Window System device
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="Solar Window System",
        model="Solar Window System",
    )

    # Check if Window Configuration entry already exists
    window_config_exists = False
    for config_entry in hass.config_entries.async_entries(DOMAIN):
        if config_entry.title == "Window Configuration":
            window_config_exists = True
            break

    # Create Window Configuration entry if it doesn't exist
    if not window_config_exists:
        await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "auto_create_window_config"},
            data={
                "entry_type": "window_configuration",
                "auto_created": True,
            },
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_setup_window_config_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Set up the Window Configuration entry."""
    device_registry = dr.async_get(hass)

    # Create Window Configuration device with its own config entry
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,  # Use its OWN config_entry_id!
        identifiers={(DOMAIN, f"{entry.entry_id}_window_config")},
        name="Window Configuration",
        manufacturer="Solar Window System",
        model="Window Configuration",
    )

    # No platforms needed for Window Configuration
    return True


async def async_setup_window_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a window configuration entry."""
    window_name = entry.data.get(CONF_WINDOW_NAME, "Window")
    window_id = entry.data.get(CONF_WINDOW, entry.entry_id)

    device_registry = dr.async_get(hass)

    # Create a device for this window with its own config entry
    # This makes each window appear as its own integration entry like openWB
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,  # Use the window's OWN config_entry_id!
        identifiers={(DOMAIN, window_id)},
        name=window_name,
        manufacturer="Solar Window System",
        model="Window",
        # No via_device - each window is independent like openWB chargepoints
    )

    # For now, we don't set up any platform entities for windows
    # This will be implemented in the future if needed
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    entry_type = entry.data.get("entry_type")

    if entry_type == ENTRY_TYPE_MAIN:
        # For main entry
        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
        if unload_ok:
            hass.data[DOMAIN].pop(entry.entry_id)
        return unload_ok
    elif entry_type == "window_configuration":
        # For Window Configuration entry, just remove the data
        if entry.entry_id in hass.data[DOMAIN]:
            hass.data[DOMAIN].pop(entry.entry_id)
        return True
    elif CONF_WINDOW_NAME in entry.data and CONF_WINDOW in entry.data:
        # For window sub-entries, just remove the data
        if entry.entry_id in hass.data[DOMAIN]:
            hass.data[DOMAIN].pop(entry.entry_id)
        return True

    # Fallback
    if entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)
    return True
