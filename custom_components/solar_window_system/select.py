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
    # Handle Global Configuration
    if entry.title == "Solar Window System":
        await _setup_global_config_selects(hass, entry, async_add_entities)
    # Handle Group Configuration subentries
    elif entry.data.get("entry_type") == "group_configs":
        await _setup_group_config_selects(hass, entry, async_add_entities)


async def _setup_global_config_selects(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Global Configuration select entities."""
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


async def _setup_group_config_selects(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Group Configuration select entities."""
    _LOGGER.info("Setting up Group Configuration select entities")

    device_registry = dr.async_get(hass)

    if not entry.subentries:
        _LOGGER.warning("No group subentries found")
        return

    select_entities = []

    # Process each group subentry
    for subentry_id, subentry in entry.subentries.items():
        if subentry.subentry_type == "group":
            group_name = subentry.title
            _LOGGER.info("Setting up select entities for group: %s", group_name)

            # Find the device for this group
            group_device = None
            for device in device_registry.devices.values():
                # Check if device belongs to this entry and subentry
                device_has_entry = (
                    device.config_entries and entry.entry_id in device.config_entries
                )
                subentries = device.config_entries_subentries
                device_has_subentry = (
                    subentries
                    and entry.entry_id in subentries
                    and subentry_id in subentries[entry.entry_id]
                )

                if device_has_entry and device_has_subentry:
                    for identifier in device.identifiers:
                        if (
                            identifier[0] == DOMAIN
                            and identifier[1] == f"group_{subentry_id}"
                        ):
                            group_device = device
                            break
                    if group_device:
                        break

            if group_device:
                # Create scenario enable select entities for this group
                select_entities.extend(
                    [
                        GroupConfigSelectEntity(
                            "scenario_b_enable",
                            {
                                "name": "Enable Scenario B",
                                "options": ["disable", "enable", "inherit"],
                                "default": "inherit",
                                "icon": "mdi:toggle-switch",
                            },
                            group_device,
                            group_name,
                            subentry_id,
                        ),
                        GroupConfigSelectEntity(
                            "scenario_c_enable",
                            {
                                "name": "Enable Scenario C",
                                "options": ["disable", "enable", "inherit"],
                                "default": "inherit",
                                "icon": "mdi:toggle-switch",
                            },
                            group_device,
                            group_name,
                            subentry_id,
                        ),
                    ]
                )
            else:
                _LOGGER.warning("Group device not found for: %s", group_name)

    if select_entities:
        async_add_entities(select_entities)
        _LOGGER.info(
            "Added %d Group Configuration select entities", len(select_entities)
        )


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
        # Use modern entity naming with has_entity_name = True
        self._attr_name = config["name"]
        self._attr_unique_id = f"{ENTITY_PREFIX_GLOBAL}_{entity_key}"
        self._attr_has_entity_name = True

        _LOGGER.warning(
            "🔧 Select %s: unique_id=%s, name=%s",
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
        _LOGGER.warning(
            "🔧 Select %s registered with name: %s",
            self._entity_key,
            self._attr_name,
        )

    async def async_select_option(self, option: str) -> None:
        """Update the current selection."""
        self._attr_current_option = option
        self.async_write_ha_state()


class GroupConfigSelectEntity(SelectEntity):
    """Select entity for group configuration scenario enables."""

    def __init__(
        self,
        entity_key: str,
        config: dict,
        device: dr.DeviceEntry,
        group_name: str,
        subentry_id: str,
    ) -> None:
        """Initialize the group select entity."""
        self._entity_key = entity_key
        self._config = config
        self._device = device
        self._group_name = group_name
        self._subentry_id = subentry_id

        # Use modern entity naming with has_entity_name = True
        self._attr_name = config["name"]
        # Create unique_id with group prefix: sws_group_<group_name>_<entity_key>
        group_slug = group_name.lower().replace(" ", "_").replace("-", "_")
        self._attr_unique_id = f"sws_group_{group_slug}_{entity_key}"
        self._attr_has_entity_name = True

        _LOGGER.warning(
            "🔧 Group Select %s: unique_id=%s, name=%s, group=%s",
            entity_key,
            self._attr_unique_id,
            self._attr_name,
            group_name,
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
        _LOGGER.warning(
            "🔧 Group Select %s registered with name: %s for group: %s",
            self._entity_key,
            self._attr_name,
            self._group_name,
        )

    async def async_select_option(self, option: str) -> None:
        """Update the current selection."""
        self._attr_current_option = option
        self.async_write_ha_state()
