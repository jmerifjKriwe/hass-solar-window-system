"""Switch entities for Solar Window System scenario configuration."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_SCENARIO_FORECAST,
    CONF_SCENARIO_INDOOR,
    CONF_SCENARIO_OUTDOOR,
    DOMAIN,
    LEVEL_GROUP,
    LEVEL_WINDOW,
)
from .coordinator import SolarCalculationCoordinator

SCENARIO_DESCRIPTIONS = {
    CONF_SCENARIO_INDOOR: SwitchEntityDescription(
        key=CONF_SCENARIO_INDOOR,
        name="Szenario: Innentemperatur",
        entity_category=EntityCategory.CONFIG,
    ),
    CONF_SCENARIO_OUTDOOR: SwitchEntityDescription(
        key=CONF_SCENARIO_OUTDOOR,
        name="Szenario: Außentemperatur",
        entity_category=EntityCategory.CONFIG,
    ),
    CONF_SCENARIO_FORECAST: SwitchEntityDescription(
        key=CONF_SCENARIO_FORECAST,
        name="Szenario: Wettervorhersage",
        entity_category=EntityCategory.CONFIG,
    ),
}

DEFAULT_SCENARIOS = {
    CONF_SCENARIO_INDOOR: True,
    CONF_SCENARIO_OUTDOOR: True,
    CONF_SCENARIO_FORECAST: True,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up switch entities from config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities = []

    # Global scenario entities
    for key, description in SCENARIO_DESCRIPTIONS.items():
        entities.append(
            SolarScenarioSwitch(
                coordinator,
                entry,
                "global",
                "global",
                key,
                description,
            )
        )

    # Group scenario entities
    for group_id in coordinator.groups:
        for key, description in SCENARIO_DESCRIPTIONS.items():
            entities.append(
                SolarScenarioSwitch(
                    coordinator,
                    entry,
                    LEVEL_GROUP,
                    group_id,
                    key,
                    description,
                )
            )

    # Window scenario entities
    for window_id in coordinator.windows:
        for key, description in SCENARIO_DESCRIPTIONS.items():
            entities.append(
                SolarScenarioSwitch(
                    coordinator,
                    entry,
                    LEVEL_WINDOW,
                    window_id,
                    key,
                    description,
                )
            )

    async_add_entities(entities)


class SolarScenarioSwitch(CoordinatorEntity, SwitchEntity):
    """Switch entity for scenario configuration with inheritance."""

    coordinator: SolarCalculationCoordinator

    def __init__(
        self,
        coordinator: SolarCalculationCoordinator,
        entry: ConfigEntry,
        level: str,
        entity_id: str,
        scenario_key: str,
        description: SwitchEntityDescription,
    ) -> None:
        """Initialize the scenario switch."""
        super().__init__(coordinator)
        self._entry = entry
        self._level = level
        self._entity_id = entity_id
        self._scenario_key = scenario_key
        self.entity_description = description

    @property
    def unique_id(self):
        """Return unique ID."""
        return f"{DOMAIN}_{self._level}_{self._entity_id}_{self._scenario_key}"

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
    def is_on(self):
        """Return the effective state (inherited or overridden)."""
        return self.coordinator.get_effective_value(
            self._level, self._entity_id, self._scenario_key
        )

    @property
    def available(self):
        """Return availability based on coordinator."""
        return self.coordinator.last_update_success

    async def async_turn_on(self, **kwargs):
        """Turn on scenario and store as override."""
        await self.coordinator.set_override(self._level, self._entity_id, self._scenario_key, True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn off scenario and store as override."""
        await self.coordinator.set_override(self._level, self._entity_id, self._scenario_key, False)
        self.async_write_ha_state()
