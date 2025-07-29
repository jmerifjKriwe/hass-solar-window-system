import pytest
from unittest.mock import MagicMock
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from custom_components.solar_window_system.switch import (
    SolarMaintenanceSwitch,
    SolarDebugSwitch,
    SolarScenarioBSwitch,
    SolarScenarioCSwitch,
)


@pytest.fixture
def mock_entry():
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    return entry


@pytest.fixture
def mock_hass():
    return MagicMock(spec=HomeAssistant)


@pytest.mark.parametrize(
    "switch_class",
    [
        SolarMaintenanceSwitch,
        SolarDebugSwitch,
        SolarScenarioBSwitch,
        SolarScenarioCSwitch,
    ],
)
def test_switch_on_off(switch_class, mock_hass, mock_entry):
    from unittest.mock import AsyncMock

    # Ensure options dict exists for all switches
    mock_entry.options = {}
    # For scenario switches, set entry.options to False so default is off
    if switch_class.__name__ == "SolarScenarioBSwitch":
        mock_entry.options = {"scenario_b_enabled": False}
    elif switch_class.__name__ == "SolarScenarioCSwitch":
        mock_entry.options = {"scenario_c_enabled": False}
    switch = switch_class(mock_hass, mock_entry)
    # Default state off
    assert not switch.is_on
    # Turn on
    mock_update = AsyncMock()
    switch._async_update_option = mock_update
    switch._attr_is_on = False
    mock_hass.async_add_job = lambda func, *args, **kwargs: func(*args, **kwargs)
    import asyncio

    asyncio.run(switch.async_turn_on())
    mock_update.assert_awaited_with(True)
    # Turn off
    mock_update.reset_mock()
    switch._attr_is_on = True
    asyncio.run(switch.async_turn_off())
    mock_update.assert_awaited_with(False)
