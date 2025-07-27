import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .calculator import SolarWindowCalculator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class SolarWindowDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Solar Window System data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, config_data: dict):
        """Initialize."""
        # Store the entry_id separately BEFORE calling super().__init__
        # because super().__init__ might clear the config_entry attribute
        self._entry_id = entry.entry_id

        _LOGGER.info(f"Coordinator initialized with entry_id: {self._entry_id}")

        # Declare calculator attribute before super().__init__ to satisfy Pylance
        self.calculator = SolarWindowCalculator(
            hass, config_data["defaults"], config_data["groups"], config_data["windows"]
        )

        update_interval_minutes = entry.options.get("update_interval", 5)
        update_interval = timedelta(minutes=update_interval_minutes)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

        # Store config_entry AFTER super().__init__ to avoid it being overwritten
        self.config_entry = entry

    async def _async_update_data(self):
        """Fetch data from the calculator."""

        latest_entry = self.hass.config_entries.async_get_entry(
            self.config_entry.entry_id
        )
        if latest_entry is None:
            _LOGGER.warning(
                "Config entry not available during coordinator refresh, skipping update."
            )
            return self.data

        current_options = {**latest_entry.data, **latest_entry.options}

        # --- KORRIGIERTE LOGIK ---
        if current_options.get("maintenance_mode", False):
            _LOGGER.info("Maintenance mode active. Keeping last known values.")

            # Wenn noch keine Daten vorhanden sind, führe eine einmalige Berechnung durch
            if self.data is None:
                _LOGGER.info(
                    "No data available yet. Performing initial calculation despite maintenance mode."
                )
                try:
                    return await self.hass.async_add_executor_job(
                        self.calculator.calculate_all_windows, current_options
                    )
                except Exception as exception:
                    raise UpdateFailed(
                        f"Error during initial calculation: {exception}"
                    ) from exception

            # Ansonsten die letzten bekannten Daten zurückgeben
            return self.data

        # Normale Berechnung wenn nicht im Maintenance-Modus
        try:
            return await self.hass.async_add_executor_job(
                self.calculator.calculate_all_windows, current_options
            )
        except Exception as exception:
            raise UpdateFailed(
                f"Error communicating with calculator: {exception}"
            ) from exception
