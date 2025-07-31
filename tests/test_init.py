"""Test the initialization of the solar_window_system component."""
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import async_get

from .conftest import setup_integration


async def test_async_setup_entry(hass: HomeAssistant, setup_integration):
    """Test a successful setup entry."""
    assert setup_integration.state == ConfigEntryState.LOADED
    # Check that the coordinator is in hass.data
    coordinator = hass.data[setup_integration.domain][setup_integration.entry_id]
    assert coordinator is not None
    assert hasattr(coordinator, "data")
