import pytest
from unittest.mock import Mock, AsyncMock
from homeassistant.core import HomeAssistant
from custom_components.solar_window_system.const import DOMAIN


@pytest.mark.asyncio
async def test_recalculate_service_triggers_all(hass: HomeAssistant):
    """Service should trigger recalculation for all windows."""
    # Setup mocks
    from unittest.mock import patch

    coordinator = Mock()
    coordinator.async_refresh = AsyncMock()
    coordinator.async_config_entry_first_refresh = AsyncMock()
    hass.data = {DOMAIN: {"entry1": {"coordinator": coordinator}}}
    hass.data["integrations"] = {}
    hass.config_entries = Mock()
    hass.config_entries.async_forward_entry_setups = AsyncMock()
    entry = Mock()
    entry.data = {"entry_type": "window_configs"}
    entry.entry_id = "entry1"
    entry.subentries = {}
    hass.config_entries.async_entries = Mock(return_value=[entry])
    with patch(
        "custom_components.solar_window_system.__init__.SolarWindowSystemCoordinator",
        return_value=coordinator,
    ):
        from custom_components.solar_window_system.__init__ import async_setup_entry

        await async_setup_entry(hass, entry)
        await hass.services.async_call(DOMAIN, "recalculate", {}, blocking=True)
    coordinator.async_refresh.assert_awaited()


@pytest.mark.asyncio
async def test_recalculate_service_triggers_specific_window(hass: HomeAssistant):
    """Service should trigger recalculation for a specific window (logic placeholder)."""
    from unittest.mock import patch

    coordinator = Mock()
    coordinator.async_refresh = AsyncMock()
    coordinator.async_config_entry_first_refresh = AsyncMock()
    hass.data = {DOMAIN: {"entry1": {"coordinator": coordinator}}}
    hass.data["integrations"] = {}
    hass.config_entries = Mock()
    hass.config_entries.async_forward_entry_setups = AsyncMock()
    entry = Mock()
    entry.data = {"entry_type": "window_configs"}
    entry.entry_id = "entry1"
    entry.subentries = {}
    hass.config_entries.async_entries = Mock(return_value=[entry])
    with patch(
        "custom_components.solar_window_system.__init__.SolarWindowSystemCoordinator",
        return_value=coordinator,
    ):
        from custom_components.solar_window_system.__init__ import async_setup_entry

        await async_setup_entry(hass, entry)
        await hass.services.async_call(
            DOMAIN, "recalculate", {"window_id": "window_1"}, blocking=True
        )
    coordinator.async_refresh.assert_awaited()


@pytest.mark.asyncio
async def test_recalculate_service_no_window_configs(hass: HomeAssistant):
    """Service should do nothing if no window_configs entry exists."""
    hass.data = {DOMAIN: {}}
    hass.config_entries = Mock()
    hass.config_entries.async_entries = Mock(return_value=[])
    from custom_components.solar_window_system.__init__ import async_setup_entry

    entry = Mock()
    entry.data = {"entry_type": "global_config"}
    entry.subentries = {}  # Fix: must be a dict for _create_subentry_devices
    await async_setup_entry(hass, entry)
    # Should not raise
    await hass.services.async_call(DOMAIN, "recalculate", {}, blocking=True)
"""Tests for the recalculate service and integration-level behavior."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN


@pytest.mark.asyncio
async def test_recalculate_service_triggers_coordinator(hass: HomeAssistant) -> None:
    """Service should call coordinator refresh when invoked."""
    # Ensure the integration is set up so services get registered
    global_entry = MockConfigEntry(domain=DOMAIN, data={"entry_type": "global_config"})
    global_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(global_entry.entry_id)

    # Prepare a fake coordinator for a window_configs entry
    coordinator = Mock()
    coordinator.async_refresh = AsyncMock()

    window_entry = MockConfigEntry(domain=DOMAIN, data={"entry_type": "window_configs"})
    window_entry.add_to_hass(hass)

    # Directly insert our mock coordinator into hass.data for the window entry
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][window_entry.entry_id] = {"coordinator": coordinator}

    # Call the service and ensure coordinator.async_refresh was awaited
    await hass.services.async_call(DOMAIN, "recalculate", {}, blocking=True)
    coordinator.async_refresh.assert_awaited()
