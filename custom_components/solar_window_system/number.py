"""Number entities for Solar Window System configuration."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_THRESHOLD_FORECAST,
    CONF_THRESHOLD_INDOOR,
    CONF_THRESHOLD_OUTDOOR,
    CONF_THRESHOLD_RADIATION,
    DEFAULT_FORECAST_HIGH,
    DEFAULT_INSIDE_TEMP,
    DEFAULT_OUTSIDE_TEMP,
    DEFAULT_SOLAR_ENERGY,
    DOMAIN,
    LEVEL_GROUP,
    LEVEL_WINDOW,
)
from .coordinator import SolarCalculationCoordinator

THRESHOLD_DESCRIPTIONS = {
    CONF_THRESHOLD_INDOOR: NumberEntityDescription(
        key=CONF_THRESHOLD_INDOOR,
        name="Innentemperatur Schwellenwert",
        native_min_value=15,
        native_max_value=35,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.CONFIG,
    ),
    CONF_THRESHOLD_OUTDOOR: NumberEntityDescription(
        key=CONF_THRESHOLD_OUTDOOR,
        name="Außentemperatur Schwellenwert",
        native_min_value=15,
        native_max_value=40,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.CONFIG,
    ),
    CONF_THRESHOLD_FORECAST: NumberEntityDescription(
        key=CONF_THRESHOLD_FORECAST,
        name="Vorhersage Temperatur Schwellenwert",
        native_min_value=15,
        native_max_value=45,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.CONFIG,
    ),
    CONF_THRESHOLD_RADIATION: NumberEntityDescription(
        key=CONF_THRESHOLD_RADIATION,
        name="Solarenergie Schwellenwert",
        native_min_value=100,
        native_max_value=1000,
        native_step=10,
        native_unit_of_measurement="W/m²",
        entity_category=EntityCategory.CONFIG,
    ),
}

DEFAULT_THRESHOLDS = {
    CONF_THRESHOLD_INDOOR: DEFAULT_INSIDE_TEMP,
    CONF_THRESHOLD_OUTDOOR: DEFAULT_OUTSIDE_TEMP,
    CONF_THRESHOLD_FORECAST: DEFAULT_FORECAST_HIGH,
    CONF_THRESHOLD_RADIATION: DEFAULT_SOLAR_ENERGY,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up number entities from config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities = []

    # Global threshold entities
    for key, description in THRESHOLD_DESCRIPTIONS.items():
        entities.append(
            SolarThresholdNumber(
                coordinator,
                entry,
                "global",
                "global",
                key,
                description,
            )
        )

    # Group threshold entities
    for group_id in coordinator.groups:
        for key, description in THRESHOLD_DESCRIPTIONS.items():
            entities.append(
                SolarThresholdNumber(
                    coordinator,
                    entry,
                    LEVEL_GROUP,
                    group_id,
                    key,
                    description,
                )
            )

    # Window threshold entities
    for window_id in coordinator.windows:
        for key, description in THRESHOLD_DESCRIPTIONS.items():
            entities.append(
                SolarThresholdNumber(
                    coordinator,
                    entry,
                    LEVEL_WINDOW,
                    window_id,
                    key,
                    description,
                )
            )

    async_add_entities(entities)


class SolarThresholdNumber(CoordinatorEntity, NumberEntity):
    """Number entity for threshold configuration with inheritance."""

    coordinator: SolarCalculationCoordinator

    def __init__(
        self,
        coordinator: SolarCalculationCoordinator,
        entry: ConfigEntry,
        level: str,
        entity_id: str,
        threshold_key: str,
        description: NumberEntityDescription,
    ) -> None:
        """Initialize the threshold number."""
        super().__init__(coordinator)
        self._entry = entry
        self._level = level
        self._entity_id = entity_id
        self._threshold_key = threshold_key
        self.entity_description = description

    @property
    def unique_id(self):
        """Return unique ID."""
        return f"{DOMAIN}_{self._level}_{self._entity_id}_{self._threshold_key}"

    @property
    def device_info(self):
        """Return device info."""
        if self._level == "global":
            return DeviceInfo(
                identifiers={(DOMAIN, "global")},
                name="Solar Window System Global",
                manufacturer="Solar Window System",
            )
        elif self._level == LEVEL_GROUP:
            group_name = self.coordinator.groups.get(self._entity_id, {}).get(
                "name", self._entity_id
            )
            return DeviceInfo(
                identifiers={(DOMAIN, f"group_{self._entity_id}")},
                name=f"Gruppe: {group_name}",
                manufacturer="Solar Window System",
                via_device=(DOMAIN, "global"),
            )
        else:  # window
            window_name = self.coordinator.windows.get(self._entity_id, {}).get(
                "name", self._entity_id
            )
            return DeviceInfo(
                identifiers={(DOMAIN, f"window_{self._entity_id}")},
                name=f"Fenster: {window_name}",
                manufacturer="Solar Window System",
                via_device=(DOMAIN, "global"),
            )

    @property
    def native_value(self):
        """Return the effective value (inherited or overridden)."""
        return self.coordinator.get_effective_value(
            self._level, self._entity_id, self._threshold_key
        )

    @property
    def available(self):
        """Return availability based on coordinator."""
        return self.coordinator.last_update_success

    async def async_set_native_value(self, value):
        """Set new value and store as override."""
        await self.coordinator.set_override(
            self._level, self._entity_id, self._threshold_key, value
        )
        self.async_write_ha_state()
