"""Test the initialization of the solar_window_system component."""
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import async_get

from .conftest import setup_integration


async def test_async_setup_entry(hass: HomeAssistant, setup_integration):
    """Test a successful setup entry."""
    assert len(hass.states.async_all()) > 0

    entity_registry = async_get(hass)

    # Check if one of the entities is created
    entry = entity_registry.async_get("sensor.solar_window_system_test_window_south_power")
    assert entry is not None

    # Check that the coordinator is in hass.data
    coordinator = hass.data[setup_integration.domain][setup_integration.entry_id]
    assert coordinator is not None
    assert hasattr(coordinator, "data")
    assert coordinator.data is not None
