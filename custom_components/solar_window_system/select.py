# /config/custom_components/solar_window_system/select.py

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import SolarWindowSystemConfigEntity

PRESET_OPTIONS = ["Normal", "Relaxed", "Sensitive", "Children", "Custom"]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the select entities."""
    async_add_entities([SolarPresetSelect(hass, entry)])


class SolarPresetSelect(SolarWindowSystemConfigEntity, SelectEntity):
    _attr_name = "Preset Mode"
    _attr_unique_id = f"{DOMAIN}_preset_mode"
    _attr_icon = "mdi:tune"
    _attr_options = PRESET_OPTIONS

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialize the select entity."""
        super().__init__(hass, entry)

    @property
    def current_option(self) -> str:
        """Return the selected entity option."""
        return self.entry.options.get("preset_mode", "Normal")

    async def async_select_option(self, option: str) -> None:
        """Change the selected option and update related number entity values."""
        options = dict(self.entry.options)
        options["preset_mode"] = option

        if option == "Relaxed":
            options["global_sensitivity"] = 0.7
            options["children_factor"] = 1.2
        elif option == "Sensitive":
            options["global_sensitivity"] = 1.5
            options["children_factor"] = 0.5
        elif option == "Children":
            options["children_factor"] = 0.3
        elif option == "Normal":
            options["global_sensitivity"] = 1.0
            options["children_factor"] = 0.8

        # This single call saves all changes and triggers the reload listener.
        self.hass.config_entries.async_update_entry(self.entry, options=options)
