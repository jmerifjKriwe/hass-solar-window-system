from homeassistant.components.switch import SwitchEntity
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
    """Set up the switch entities."""
    if entry.data.get(CONF_ENTRY_TYPE) == "global":
        entities = [
            SolarMaintenanceSwitch(hass, entry),
            SolarDebugSwitch(hass, entry),
            SolarScenarioBSwitch(hass, entry),
            SolarScenarioCSwitch(hass, entry),
        ]
        async_add_entities(entities)


class BaseSwitchEntity(SolarWindowSystemConfigEntity, SwitchEntity):
    """Base class for our switch entities."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, key: str, default: bool
    ):
        super().__init__(hass, entry)
        self._key = key
        self._default = default

    @property
    def is_on(self) -> bool:
        """Return the state of the entity from the config entry options."""
        return self.entry.options.get(self._key, self._default)

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        options = dict(self.entry.options)
        options[self._key] = True
        self.hass.config_entries.async_update_entry(self.entry, options=options)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the entity off."""
        options = dict(self.entry.options)
        options[self._key] = False
        self.hass.config_entries.async_update_entry(self.entry, options=options)


class SolarMaintenanceSwitch(BaseSwitchEntity):
    _attr_name = "Beschattungsautomatik pausieren"
    _attr_icon = "mdi:pause-circle-outline"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, entry, "maintenance_mode", False)
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_automatic_paused"


class SolarDebugSwitch(BaseSwitchEntity):
    _attr_name = "Debug Mode"
    _attr_icon = "mdi:bug"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, entry, "debug_mode", False)
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_debug_mode"


class SolarScenarioBSwitch(BaseSwitchEntity):
    _attr_name = "Scenario B Enabled"
    _attr_icon = "mdi:weather-cloudy"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, entry, "scenario_b_enabled", False)
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_scenario_b_enabled"


class SolarScenarioCSwitch(BaseSwitchEntity):
    _attr_name = "Scenario C Enabled"
    _attr_icon = "mdi:white-balance-sunny"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, entry, "scenario_c_enabled", False)
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_scenario_c_enabled"
