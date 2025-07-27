# /config/custom_components/solar_window_system/switch.py

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import SolarWindowSystemConfigEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the switch entities."""
    async_add_entities(
        [
            SolarMaintenanceSwitch(hass, entry),
            SolarDebugSwitch(hass, entry),
            SolarScenarioBSwitch(hass, entry),
            SolarScenarioCSwitch(hass, entry),
        ]
    )


class BaseSwitchEntity(SolarWindowSystemConfigEntity, SwitchEntity):
    """Base class for our switch entities."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, key: str, default: bool
    ):
        super().__init__(hass, entry)
        self._key = key
        self._default = default
        self._attr_should_poll = False

    @property
    def is_on(self) -> bool:
        """Return the state of the entity."""
        return self.entry.options.get(self._key, self._default)

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        await self._async_update_option(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the entity off."""
        await self._async_update_option(False)

    async def _async_update_option(self, value: bool) -> None:
        """Update the config entry option."""
        options = dict(self.entry.options)
        options[self._key] = value
        self.hass.config_entries.async_update_entry(self.entry, options=options)


class SolarMaintenanceSwitch(BaseSwitchEntity):
    _attr_name = "Maintenance Mode"
    _attr_unique_id = f"{DOMAIN}_maintenance_mode"
    _attr_icon = "mdi:auto-fix"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, entry, "maintenance_mode", False)


class SolarDebugSwitch(BaseSwitchEntity):
    _attr_name = "Debug Mode"
    _attr_unique_id = f"{DOMAIN}_debug_mode"
    _attr_icon = "mdi:bug"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, entry, "debug_mode", False)


class SolarScenarioBSwitch(BaseSwitchEntity):
    _attr_name = "Scenario B Enabled"
    _attr_unique_id = f"{DOMAIN}_scenario_b_enabled"
    _attr_icon = "mdi:weather-cloudy"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, entry, "scenario_b_enabled", True)


class SolarScenarioCSwitch(BaseSwitchEntity):
    _attr_name = "Scenario C Enabled"
    _attr_unique_id = f"{DOMAIN}_scenario_c_enabled"
    _attr_icon = "mdi:white-balance-sunny"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, entry, "scenario_c_enabled", True)
