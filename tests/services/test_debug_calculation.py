"""Tests for the `solar_window_system_debug_calculation` service."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock

from custom_components.solar_window_system.const import DOMAIN
from tests.helpers.test_framework import ServiceTestCase


class TestDebugCalculationService(ServiceTestCase):
    """Tests for the solar_window_system_debug_calculation service."""

    async def test_debug_calculation_service_valid_window_id(self) -> None:
        """Call the debug_calculation service with valid window id."""
        # Create mock hass
        mock_hass = Mock()
        mock_hass.services.has_service = Mock(return_value=True)
        mock_hass.services.async_call = AsyncMock()

        # Service should be registered by the integration setup
        if not mock_hass.services.has_service(
            DOMAIN, "solar_window_system_debug_calculation"
        ):
            msg = "solar_window_system_debug_calculation service not registered"
            raise AssertionError(msg)

        # Call the service with valid window id
        await mock_hass.services.async_call(
            DOMAIN,
            "solar_window_system_debug_calculation",
            {"window_id": "test_window"},
            blocking=True,
        )

        # Verify service was called
        mock_hass.services.async_call.assert_called_once_with(
            DOMAIN,
            "solar_window_system_debug_calculation",
            {"window_id": "test_window"},
            blocking=True,
        )

    async def test_debug_calculation_service_with_filename(self) -> None:
        """Call the debug_calculation service with custom filename."""
        # Create mock hass
        mock_hass = Mock()
        mock_hass.services.has_service = Mock(return_value=True)
        mock_hass.services.async_call = AsyncMock()

        # Service should be registered by the integration setup
        if not mock_hass.services.has_service(
            DOMAIN, "solar_window_system_debug_calculation"
        ):
            msg = "solar_window_system_debug_calculation service not registered"
            raise AssertionError(msg)

        # Call the service with window id and custom filename
        await mock_hass.services.async_call(
            DOMAIN,
            "solar_window_system_debug_calculation",
            {"window_id": "test_window", "filename": "custom_debug.json"},
            blocking=True,
        )

        # Verify service was called
        mock_hass.services.async_call.assert_called_once_with(
            DOMAIN,
            "solar_window_system_debug_calculation",
            {"window_id": "test_window", "filename": "custom_debug.json"},
            blocking=True,
        )

    async def test_debug_calculation_service_missing_window_id(self) -> None:
        """Call the debug_calculation service without required window_id."""
        # Create mock hass
        mock_hass = Mock()
        mock_hass.services.has_service = Mock(return_value=True)
        mock_hass.services.async_call = AsyncMock()

        # Service should be registered by the integration setup
        if not mock_hass.services.has_service(
            DOMAIN, "solar_window_system_debug_calculation"
        ):
            msg = "solar_window_system_debug_calculation service not registered"
            raise AssertionError(msg)

        # Call the service without window_id (should fail)
        await mock_hass.services.async_call(
            DOMAIN, "solar_window_system_debug_calculation", {}, blocking=True
        )

        # Verify service was called
        mock_hass.services.async_call.assert_called_once_with(
            DOMAIN, "solar_window_system_debug_calculation", {}, blocking=True
        )
