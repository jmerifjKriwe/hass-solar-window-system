"""Data update coordinator for Solar Window System."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .calculator import SolarWindowCalculator
from .const import DOMAIN

if TYPE_CHECKING:  # pragma: no cover
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class SolarWindowSystemCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching solar window system data."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        update_interval_minutes: int,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(minutes=update_interval_minutes),
        )
        self.entry = entry
        self.calculator: SolarWindowCalculator | None = None
        self._setup_calculator()

    def _setup_calculator(self) -> None:
        """Set up the calculator with flow-based configuration."""
        try:
            # Initialize calculator with flow-based configuration
            self.calculator = SolarWindowCalculator.from_flows(self.hass, self.entry)
        except (ValueError, TypeError, AttributeError):
            _LOGGER.exception("Failed to initialize calculator")
            self.calculator = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the calculator."""
        if not self.calculator:
            _LOGGER.warning("Calculator not initialized, skipping update")
            return {}

        try:
            # Use the new flow-based calculation method
            results = self.calculator.calculate_all_windows_from_flows()
        except (ValueError, TypeError, AttributeError) as err:
            _LOGGER.exception("Error updating solar window data")
            msg = f"Error updating solar window data: {err}"
            raise UpdateFailed(msg) from err
        else:
            _LOGGER.debug(
                "Calculator update completed with %d window results",
                len(results.get("windows", {})),
            )
            # Ensure stable shape for consumers/tests
            if "windows" not in results:
                results["windows"] = {}
            if "groups" not in results:
                results["groups"] = {}
            return results

    def get_window_shading_status(self, window_name: str) -> bool:
        """Get shading status for a specific window."""
        if not self.data:
            return False

        windows = self.data.get("windows", {})
        window_data = windows.get(window_name, {})
        return window_data.get("requires_shading", False)

    def get_window_data(self, window_name: str) -> dict[str, Any]:
        """Get all data for a specific window."""
        if not self.data:
            return {}

        windows = self.data.get("windows", {})
        return windows.get(window_name, {})

    async def async_reconfigure(self) -> None:
        """Reconfigure the coordinator when config changes."""
        self._setup_calculator()
        await self.async_refresh()

    async def create_debug_data(self, window_id: str) -> dict[str, Any] | None:
        """Create comprehensive debug data for a window."""
        if not self.calculator:
            _LOGGER.warning("Calculator not initialized")
            return None

        try:
            # Get debug data from calculator
            debug_data = self.calculator.create_debug_data(window_id)
            if debug_data:
                # Add coordinator metadata
                debug_data["metadata"] = {
                    "coordinator_entry_id": self.entry.entry_id,
                    "coordinator_name": self.name,
                    "update_interval_minutes": (
                        self.update_interval.total_seconds() / 60
                        if self.update_interval
                        else 0
                    ),
                    "last_update": datetime.now(UTC).isoformat(),
                    "next_update": (
                        (datetime.now(UTC) + self.update_interval).isoformat()
                        if self.update_interval
                        else None
                    ),
                }

                return debug_data

            _LOGGER.warning("No debug data found for window: %s", window_id)

        except Exception as err:
            _LOGGER.exception("Error creating debug data for window %s", window_id)
            return {
                "error": str(err),
                "window_id": window_id,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        else:
            return None
