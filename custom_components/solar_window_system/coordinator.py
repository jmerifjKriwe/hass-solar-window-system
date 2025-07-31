import logging
import asyncio
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
        self._entry_id = entry.entry_id
        # config_data now directly contains the global configuration
        self.calculator = SolarWindowCalculator(hass, config_data)
        self._first_refresh_lock = asyncio.Lock()

        update_interval_minutes = entry.options.get("update_interval", 5)
        update_interval = timedelta(minutes=update_interval_minutes)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

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

        current_options = latest_entry.options

        if current_options.get("maintenance_mode", False):
            _LOGGER.info("Maintenance mode active. Keeping last known values.")
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
            return self.data

        try:
            return await self.hass.async_add_executor_job(
                self.calculator.calculate_all_windows, current_options
            )
        except Exception as exception:
            raise UpdateFailed(
                f"Error communicating with calculator: {exception}"
            ) from exception

    async def async_config_entry_first_refresh(self) -> None:
        """Perform the first refresh of the coordinator data."""
        async with self._first_refresh_lock:
            if self.data is not None:
                return

            _LOGGER.debug("Performing first refresh for %s", self.name)
            await self.async_refresh()

            if self.data is None:
                raise UpdateFailed(f"Initial refresh failed for {self.name}")

            _LOGGER.debug("First refresh for %s complete", self.name)