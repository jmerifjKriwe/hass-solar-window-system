# /config/custom_components/solar_window_system/number.py

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import SolarWindowSystemConfigEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the number entities."""
    async_add_entities(
        [
            # Existing entities
            SolarGlobalSensitivityNumber(hass, entry),
            SolarChildrenFactorNumber(hass, entry),
            SolarTemperatureOffsetNumber(hass, entry),
            # Physical properties
            SolarGValueNumber(hass, entry),
            SolarFrameWidthNumber(hass, entry),
            SolarDiffuseFactorNumber(hass, entry),
            SolarTiltNumber(hass, entry),
            # Thresholds
            SolarThresholdDirectNumber(hass, entry),
            SolarThresholdDiffuseNumber(hass, entry),
            # Base temperatures
            SolarTempIndoorBaseNumber(hass, entry),
            SolarTempOutdoorBaseNumber(hass, entry),
            # Scenario B
            SolarScenarioBTempIndoorOffsetNumber(hass, entry),
            SolarScenarioBTempOutdoorOffsetNumber(hass, entry),
            # Scenario C
            SolarScenarioCTempForecastThresholdNumber(hass, entry),
            SolarScenarioCStartHourNumber(hass, entry),
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
        """Update the current value and set preset mode to Custom."""
        options = dict(self.entry.options)
        options[self._key] = value

        # Set preset mode to Custom, unless it's already Custom
        if options.get("preset_mode") != "Custom":
            options["preset_mode"] = "Custom"

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


# Physical properties
class SolarGValueNumber(BaseNumberEntity):
    _attr_name = "G-Value (Energiedurchlassgrad)"
    _attr_unique_id = f"{DOMAIN}_g_value"
    _attr_icon = "mdi:brightness-7"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0.1
    _attr_native_max_value = 0.9
    _attr_native_step = 0.01

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, entry, "g_value", 0.5)


class SolarFrameWidthNumber(BaseNumberEntity):
    _attr_name = "Frame Width"
    _attr_unique_id = f"{DOMAIN}_frame_width"
    _attr_icon = "mdi:border-outside"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0.05
    _attr_native_max_value = 0.3
    _attr_native_step = 0.005
    _attr_native_unit_of_measurement = "m"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, entry, "frame_width", 0.125)


class SolarDiffuseFactorNumber(BaseNumberEntity):
    _attr_name = "Diffuse Factor"
    _attr_unique_id = f"{DOMAIN}_diffuse_factor"
    _attr_icon = "mdi:weather-cloudy"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0.05
    _attr_native_max_value = 0.5
    _attr_native_step = 0.01

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, entry, "diffuse_factor", 0.15)


class SolarTiltNumber(BaseNumberEntity):
    _attr_name = "Window Tilt"
    _attr_unique_id = f"{DOMAIN}_tilt"
    _attr_icon = "mdi:angle-acute"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0
    _attr_native_max_value = 90
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "°"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, entry, "tilt", 90)


# Thresholds
class SolarThresholdDirectNumber(BaseNumberEntity):
    _attr_name = "Direct Radiation Threshold"
    _attr_unique_id = f"{DOMAIN}_threshold_direct"
    _attr_icon = "mdi:weather-sunny"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 50
    _attr_native_max_value = 1000
    _attr_native_step = 10
    _attr_native_unit_of_measurement = "W/m²"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, entry, "threshold_direct", 200)


class SolarThresholdDiffuseNumber(BaseNumberEntity):
    _attr_name = "Diffuse Radiation Threshold"
    _attr_unique_id = f"{DOMAIN}_threshold_diffuse"
    _attr_icon = "mdi:weather-partly-cloudy"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 30
    _attr_native_max_value = 800
    _attr_native_step = 10
    _attr_native_unit_of_measurement = "W/m²"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, entry, "threshold_diffuse", 150)


# Base temperatures
class SolarTempIndoorBaseNumber(BaseNumberEntity):
    _attr_name = "Base Indoor Temperature"
    _attr_unique_id = f"{DOMAIN}_temp_indoor_base"
    _attr_icon = "mdi:home-thermometer"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 18.0
    _attr_native_max_value = 28.0
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = "°C"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, entry, "temp_indoor_base", 23.0)


class SolarTempOutdoorBaseNumber(BaseNumberEntity):
    _attr_name = "Base Outdoor Temperature"
    _attr_unique_id = f"{DOMAIN}_temp_outdoor_base"
    _attr_icon = "mdi:thermometer"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 15.0
    _attr_native_max_value = 30.0
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = "°C"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, entry, "temp_outdoor_base", 19.5)


# Scenario B
class SolarScenarioBTempIndoorOffsetNumber(BaseNumberEntity):
    _attr_name = "Scenario B Indoor Temp Offset"
    _attr_unique_id = f"{DOMAIN}_scenario_b_temp_indoor_offset"
    _attr_icon = "mdi:home-thermometer-outline"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0.0
    _attr_native_max_value = 3.0
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = "°C"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, entry, "scenario_b_temp_indoor_offset", 0.5)


class SolarScenarioBTempOutdoorOffsetNumber(BaseNumberEntity):
    _attr_name = "Scenario B Outdoor Temp Offset"
    _attr_unique_id = f"{DOMAIN}_scenario_b_temp_outdoor_offset"
    _attr_icon = "mdi:thermometer-chevron-up"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 3.0
    _attr_native_max_value = 15.0
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = "°C"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, entry, "scenario_b_temp_outdoor_offset", 6.0)


# Scenario C
class SolarScenarioCTempForecastThresholdNumber(BaseNumberEntity):
    _attr_name = "Scenario C Forecast Threshold"
    _attr_unique_id = f"{DOMAIN}_scenario_c_temp_forecast_threshold"
    _attr_icon = "mdi:weather-sunny-alert"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 25.0
    _attr_native_max_value = 40.0
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = "°C"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, entry, "scenario_c_temp_forecast_threshold", 28.5)


class SolarScenarioCStartHourNumber(BaseNumberEntity):
    _attr_name = "Scenario C Start Hour"
    _attr_unique_id = f"{DOMAIN}_scenario_c_start_hour"
    _attr_icon = "mdi:clock-time-nine"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 6
    _attr_native_max_value = 12
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "h"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        super().__init__(hass, entry, "scenario_c_start_hour", 9)
