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
        """Return the currently selected option, determining if it's Custom."""
        options = self.entry.options
        sensitivity = options.get("global_sensitivity", 1.0)
        children_factor = options.get("children_factor", 0.8)

        # Check if current values match any known preset
        if sensitivity == 1.0 and children_factor == 0.8:
            return "Normal"
        elif sensitivity == 0.7 and children_factor == 1.2:
            return "Relaxed"
        elif sensitivity == 1.5 and children_factor == 0.5:
            return "Sensitive"
        elif children_factor == 0.3:
            # Simplified check for Children preset for this example
            return "Children"
        else:
            return "Custom"

    async def async_select_option(self, option: str) -> None:
        """Change the selected option and update related number entity values."""
        if option not in PRESET_OPTIONS[:-1]:  # 'Custom' darf nicht direkt gesetzt werden
            raise ValueError(f"Ungültiges Preset: {option}. Gültige Optionen: {PRESET_OPTIONS[:-1]}")

        options = dict(self.entry.options)
        options["preset_mode"] = option  # Save the selected preset name

        # If a specific preset is chosen, apply its values
        if option == "Relaxed":
            options["global_sensitivity"] = 0.7
            options["children_factor"] = 1.2
        elif option == "Sensitive":
            options["global_sensitivity"] = 1.5
            options["children_factor"] = 0.5
        elif option == "Children":
            # Set a default sensitivity if switching to Children mode
            options["global_sensitivity"] = 1.0
            options["children_factor"] = 0.3
        elif option == "Normal":
            options["global_sensitivity"] = 1.0
            options["children_factor"] = 0.8

        # This single call saves all changes and triggers the reload listener.
        self.hass.config_entries.async_update_entry(self.entry, options=options)
