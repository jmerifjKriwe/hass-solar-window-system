"""Select platform for Solar Window System."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.select import SelectEntity
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .const import DOMAIN, ENTITY_PREFIX_GLOBAL, GLOBAL_CONFIG_ENTITIES

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up select entities for Solar Window System."""
    # Only handle Global Configuration
    if entry.title != "Solar Window System":
        return

    _LOGGER.info("Setting up Global Configuration select entities")

    device_registry = dr.async_get(hass)
    global_device = None

    # Find the global configuration device
    for device in device_registry.devices.values():
        if device.config_entries and entry.entry_id in device.config_entries:
            for identifier in device.identifiers:
                if identifier[0] == DOMAIN and identifier[1] == "global_config":
                    global_device = device
                    break
            if global_device:
                break

    if global_device:
        # Get available entities for selectors
        binary_sensors = await _get_binary_sensor_entities(hass)
        input_booleans = await _get_input_boolean_entities(hass)
        temperature_sensors = await _get_temperature_sensor_entities(hass)

        select_entities = []
        for entity_key, config in GLOBAL_CONFIG_ENTITIES.items():
            if config["platform"] == "input_select":
                # Update options for specific selectors
                updated_config = config.copy()
                if entity_key == "weather_warning_sensor":
                    updated_config["options"] = ["", *binary_sensors, *input_booleans]
                elif entity_key == "weather_forecast_temperature_sensor":
                    updated_config["options"] = ["", *temperature_sensors]

                select_entities.append(
                    GlobalConfigSelectEntity(entity_key, updated_config, global_device)
                )

        if select_entities:
            async_add_entities(select_entities)
            _LOGGER.info(
                "Added %d Global Configuration select entities", len(select_entities)
            )
    else:
        _LOGGER.warning("Global Configuration device not found")


async def _get_binary_sensor_entities(hass: HomeAssistant) -> list[str]:
    """Get all binary_sensor entities."""
    entity_registry = er.async_get(hass)
    return [
        entry.entity_id
        for entry in entity_registry.entities.values()
        if entry.entity_id.startswith("binary_sensor.")
        and not entry.disabled_by
        and not entry.hidden_by
    ]


async def _get_input_boolean_entities(hass: HomeAssistant) -> list[str]:
    """Get all input_boolean entities."""
    entity_registry = er.async_get(hass)
    return [
        entry.entity_id
        for entry in entity_registry.entities.values()
        if entry.entity_id.startswith("input_boolean.")
        and not entry.disabled_by
        and not entry.hidden_by
    ]


async def _get_temperature_sensor_entities(hass: HomeAssistant) -> list[str]:
    """Get all temperature sensor entities."""
    entity_registry = er.async_get(hass)
    temperature_entities = []

    for entry in entity_registry.entities.values():
        if (
            entry.entity_id.startswith("sensor.")
            and not entry.disabled_by
            and not entry.hidden_by
        ):
            # Check if it's a temperature sensor by looking at state
            state = hass.states.get(entry.entity_id)
            if state and state.attributes.get("unit_of_measurement") in [
                "°C",
                "°F",
                "K",
            ]:
                temperature_entities.append(entry.entity_id)

    return temperature_entities


class GlobalConfigSelectEntity(SelectEntity):
    """Select entity for global configuration values."""

    def __init__(
        self,
        entity_key: str,
        config: dict,
        device: dr.DeviceEntry,
    ) -> None:
        """Initialize the select entity."""
        self._entity_key = entity_key
        self._config = config
        self._device = device
        # Set name, unique_id, and suggested_object_id for proper entity ID generation
        # WORKAROUND: Use prefixed name initially to get correct entity_id generation
        self._attr_name = f"{ENTITY_PREFIX_GLOBAL.upper()} {config['name']}"
        self._attr_unique_id = f"{ENTITY_PREFIX_GLOBAL}_{entity_key}"
        # Use suggested_object_id instead of entity_id to preserve prefix with unique_id
        self._attr_suggested_object_id = f"{ENTITY_PREFIX_GLOBAL}_{entity_key}"
        # Disable has_entity_name to ensure our suggested_object_id is used
        self._attr_has_entity_name = False
        # Store the original name for later restoration
        self._original_name = config["name"]

        _LOGGER.warning(
            "🔧 Select %s: unique_id=%s, temp_name=%s",
            entity_key,
            self._attr_unique_id,
            self._attr_name,
        )
        self._attr_device_info = {
            "identifiers": device.identifiers,
            "name": device.name,
            "manufacturer": device.manufacturer,
            "model": device.model,
        }
        self._attr_options = config["options"]
        self._attr_icon = config.get("icon")
        # Set current option to default if it's in the options list
        if config["default"] and config["default"] in config["options"]:
            self._attr_current_option = config["default"]
        else:
            self._attr_current_option = (
                config["options"][0] if config["options"] else None
            )

    async def async_added_to_hass(self) -> None:
        """Call when entity is added to hass."""
        await super().async_added_to_hass()
        # Restore the original name after entity ID has been generated
        self._attr_name = self._original_name
        _LOGGER.warning(
            "🔧 Select %s registered, restoring name to: %s",
            self._entity_key,
            self._attr_name,
        )

    async def async_select_option(self, option: str) -> None:
        """Update the current selection."""
        self._attr_current_option = option
        self.async_write_ha_state()
