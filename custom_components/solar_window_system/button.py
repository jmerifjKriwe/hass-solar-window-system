"""Button entities for Solar Window System reset functionality."""

from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LEVEL_GROUP, LEVEL_WINDOW

if TYPE_CHECKING:
    from .coordinator import SolarCalculationCoordinator

RESET_DESCRIPTION = ButtonEntityDescription(
    key="reset_overrides",
    name="Overrides zurücksetzen",
    entity_category=EntityCategory.CONFIG,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up button entities from config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities = []

    # Group reset buttons
    for group_id in coordinator.groups:
        entities.append(
            SolarResetButton(
                coordinator,
                entry,
                LEVEL_GROUP,
                group_id,
                RESET_DESCRIPTION,
            )
        )

    # Window reset buttons
    for window_id in coordinator.windows:
        entities.append(
            SolarResetButton(
                coordinator,
                entry,
                LEVEL_WINDOW,
                window_id,
                RESET_DESCRIPTION,
            )
        )

    async_add_entities(entities)


class SolarResetButton(CoordinatorEntity, ButtonEntity):
    """Button entity to reset overrides for a window or group."""

    coordinator: SolarCalculationCoordinator

    def __init__(
        self,
        coordinator: SolarCalculationCoordinator,
        entry: ConfigEntry,
        level: str,
        entity_id: str,
        description: ButtonEntityDescription,
    ):
        """Initialize the reset button."""
        super().__init__(coordinator)
        self._entry = entry
        self._level = level
        self._entity_id = entity_id
        self.entity_description = description

    @property
    def unique_id(self):
        """Return unique ID."""
        return f"{DOMAIN}_{self._level}_{self._entity_id}_reset_overrides"

    @property
    def device_info(self):
        """Return device info."""
        if self._level == LEVEL_GROUP:
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
    def available(self):
        """Return availability based on coordinator."""
        return self.coordinator.last_update_success

    async def async_press(self) -> None:
        """Handle button press - clear overrides."""
        await self.coordinator.clear_overrides(self._level, self._entity_id)
        self.async_write_ha_state()
