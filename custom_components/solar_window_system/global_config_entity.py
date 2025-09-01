"""Base class for global configuration entities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, ENTITY_PREFIX_GLOBAL, GLOBAL_CONFIG_ENTITIES

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


class GlobalConfigEntityBase(RestoreEntity):
    """Base class for all global configuration entities."""

    def __init__(
        self,
        entity_key: str,
        config: dict,
        device: dr.DeviceEntry,
    ) -> None:
        """Initialize the global config entity."""
        self._entity_key = entity_key
        self._config = config
        self._device = device

        # Set common attributes
        self._attr_unique_id = f"{ENTITY_PREFIX_GLOBAL}_{entity_key}"
        self._attr_suggested_object_id = f"{ENTITY_PREFIX_GLOBAL}_{entity_key}"
        self._attr_name = f"SWS_GLOBAL {config['name']}"
        self._attr_has_entity_name = False
        self._attr_device_info = {
            "identifiers": device.identifiers,
            "name": device.name,
            "manufacturer": device.manufacturer,
            "model": device.model,
        }

        # Set icon if provided
        if "icon" in config:
            self._attr_icon = config["icon"]

    async def async_added_to_hass(self) -> None:
        """Call when entity is added to hass and restore previous state if available."""
        await super().async_added_to_hass()

        # Set friendly name to config['name']
        entity_registry = er.async_get(self.hass)
        if self.entity_id in entity_registry.entities:
            ent_reg_entry = entity_registry.entities[self.entity_id]
            new_friendly_name = self._config.get("name")
            if ent_reg_entry.original_name != new_friendly_name:
                entity_registry.async_update_entity(
                    self.entity_id, name=new_friendly_name
                )


def find_global_config_device(
    hass: HomeAssistant,
    entry_id: str,
) -> dr.DeviceEntry | None:
    """Find the global configuration device for the given entry."""
    device_registry = dr.async_get(hass)

    for device in device_registry.devices.values():
        if device.config_entries and entry_id in device.config_entries:
            for identifier in device.identifiers:
                if identifier[0] == DOMAIN and identifier[1] == "global_config":
                    return device
    return None


def create_global_config_entities(
    entity_class: type,
    device: dr.DeviceEntry,
    platform_filter: str,
) -> list:
    """Create global config entities for the specified platform."""
    entities = []
    for entity_key, config in GLOBAL_CONFIG_ENTITIES.items():
        if config["platform"] == platform_filter:
            entities.append(entity_class(entity_key, config, device))
    return entities


async def get_temperature_sensor_entities(hass: Any) -> list[dict]:
    """
    Collect temperature sensor options for selectors.

    Returns a list of option dicts with keys:
      - value: the entity_id (what gets saved)
      - label: the friendly name to show in the UI

    Keeps filtering logic from before but exposes friendly names so the
    selector can display user-friendly labels while returning the entity_id
    when selected.
    """
    entity_registry = er.async_get(hass)
    options: list[dict] = []

    # Add an explicit "inherit" option displayed in the UI as "-1" value.
    # The label is provided via translation in the front-end; use a safe
    # fallback label here in case translations aren't loaded at call time.
    try:
        inherit_label = await hass.helpers.translation.async_gettext(
            "options.step.global_basic.data_description.option_inherit"
        )
    except (AttributeError, TypeError):
        # If translation helper isn't available in this context, use fallback.
        # TypeError can be raised if the translation key is not found.
        inherit_label = "Inherit (use parent value)"
    options.append({"value": "-1", "label": str(inherit_label)})

    for ent in entity_registry.entities.values():
        if (
            ent.entity_id.startswith("sensor.")
            and not ent.disabled_by
            and not ent.hidden_by
        ):
            state = hass.states.get(ent.entity_id)
            if state and state.attributes.get("unit_of_measurement") in (
                "°C",
                "°F",
                "K",
            ):
                label = (
                    state.name or state.attributes.get("friendly_name") or ent.entity_id
                )
                options.append({"value": ent.entity_id, "label": str(label)})

    return options
