"""Integration tests for Solar Window System services."""

from __future__ import annotations

import pytest
from typing import TYPE_CHECKING

from custom_components.solar_window_system.const import DOMAIN
from homeassistant.helpers import device_registry as dr

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.mark.asyncio
class TestServicesIntegration:
    """Integration tests for Solar Window System services."""

    async def test_services_registered_on_setup(
        self, hass: HomeAssistant, global_config_entry: MockConfigEntry
    ) -> None:
        """Test that services are properly registered during integration setup."""
        # Set up the integration
        assert await hass.config_entries.async_setup(global_config_entry.entry_id)
        await hass.async_block_till_done()

        # Verify services are registered
        assert hass.services.has_service(DOMAIN, "solar_window_system_recalculate")
        assert hass.services.has_service(
            DOMAIN, "solar_window_system_debug_calculation"
        )

    async def test_recalculate_service_integration(
        self, hass: HomeAssistant, global_config_entry: MockConfigEntry
    ) -> None:
        """Test recalculate service in full integration context."""
        # Set up the integration
        assert await hass.config_entries.async_setup(global_config_entry.entry_id)
        await hass.async_block_till_done()

        # Call the service
        await hass.services.async_call(
            DOMAIN, "solar_window_system_recalculate", {}, blocking=True
        )

        # Service should complete without errors
        await hass.async_block_till_done()

    async def test_debug_calculation_service_integration(
        self, hass: HomeAssistant, global_config_entry: MockConfigEntry
    ) -> None:
        """Test debug_calculation service in full integration context."""
        # Set up the integration
        assert await hass.config_entries.async_setup(global_config_entry.entry_id)
        await hass.async_block_till_done()

        # Call the service with a test window ID
        await hass.services.async_call(
            DOMAIN,
            "solar_window_system_debug_calculation",
            {"window_id": "test_window"},
            blocking=True,
        )

        # Service should complete without errors
        await hass.async_block_till_done()

    async def test_services_persist_across_restarts(
        self, hass: HomeAssistant, global_config_entry: MockConfigEntry
    ) -> None:
        """Test that services remain registered after config entry reload."""
        # Set up the integration
        assert await hass.config_entries.async_setup(global_config_entry.entry_id)
        await hass.async_block_till_done()

        # Verify services are registered
        assert hass.services.has_service(DOMAIN, "solar_window_system_recalculate")
        assert hass.services.has_service(
            DOMAIN, "solar_window_system_debug_calculation"
        )

        # Reload the config entry
        await hass.config_entries.async_reload(global_config_entry.entry_id)
        await hass.async_block_till_done()

        # Verify services are still registered after reload
        assert hass.services.has_service(DOMAIN, "solar_window_system_recalculate")
        assert hass.services.has_service(
            DOMAIN, "solar_window_system_debug_calculation"
        )

    async def test_services_with_device_registry(
        self, hass: HomeAssistant, global_config_entry: MockConfigEntry
    ) -> None:
        """Test services work correctly with device registry integration."""
        device_registry = dr.async_get(hass)

        # Set up the integration
        assert await hass.config_entries.async_setup(global_config_entry.entry_id)
        await hass.async_block_till_done()

        # Verify device was created
        devices = dr.async_entries_for_config_entry(
            device_registry, global_config_entry.entry_id
        )
        assert len(devices) > 0

        # Services should still work with device registry present
        await hass.services.async_call(
            DOMAIN, "solar_window_system_recalculate", {}, blocking=True
        )
        await hass.async_block_till_done()

        await hass.services.async_call(
            DOMAIN,
            "solar_window_system_debug_calculation",
            {"window_id": "test_window"},
            blocking=True,
        )
        await hass.async_block_till_done()
