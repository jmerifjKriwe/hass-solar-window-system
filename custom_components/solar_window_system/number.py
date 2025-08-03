from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_ENTRY_TYPE, DOMAIN
from .entity import SolarWindowSystemConfigEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the number entities."""
    if entry.data.get(CONF_ENTRY_TYPE) == "global":
        async_add_entities(
            [
                SolarGlobalSensitivityNumber(hass, entry),
                SolarChildrenFactorNumber(hass, entry),
                SolarTemperatureOffsetNumber(hass, entry),
            ]
        )


class BaseNumberEntity(SolarWindowSystemConfigEntity, NumberEntity):
    """Base class for our number entities."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, key: str, default: float
    ):
        super().__init__(hass, entry)
        self._key = key
        self._default = default

    @property
    def native_value(self) -> float:
        """Return the state of the entity from the config entry options."""
        return self.entry.options.get(self._key, self._default)

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        options = dict(self.entry.options)
        options[self._key] = max(
            self.native_min_value, min(self.native_max_value, value)
        )
        self.hass.config_entries.async_update_entry(self.entry, options=options)


# Existing entities
class SolarGlobalSensitivityNumber(BaseNumberEntity):
    _attr_name = "Global Sensitivity"
    _attr_unique_id = f"{DOMAIN}_global_sensitivity"
    _attr_icon = "mdi:brightness-6"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0.5
    _attr_native_max_value = 2.0
    _attr_native_step = 0.1

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, entry, "global_sensitivity", 1.0)


class SolarChildrenFactorNumber(BaseNumberEntity):
    _attr_name = "Children Factor"
    _attr_unique_id = f"{DOMAIN}_children_factor"
    _attr_icon = "mdi:human-child"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0.3
    _attr_native_max_value = 1.5
    _attr_native_step = 0.1

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, entry, "children_factor", 0.8)


class SolarTemperatureOffsetNumber(BaseNumberEntity):
    _attr_name = "Temperature Offset"
    _attr_unique_id = f"{DOMAIN}_temperature_offset"
    _attr_icon = "mdi:thermometer-plus"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = -5.0
    _attr_native_max_value = 5.0
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = "°C"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, entry, "temperature_offset", 0.0)
