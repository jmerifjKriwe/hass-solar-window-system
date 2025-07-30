import pytest
from unittest.mock import MagicMock
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from custom_components.solar_window_system.switch import (
    async_setup_entry,
    SolarMaintenanceSwitch,
    SolarDebugSwitch,
    SolarScenarioBSwitch,
    SolarScenarioCSwitch,
)
from custom_components.solar_window_system.const import DOMAIN


@pytest.fixture
def mock_entry():
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.options = {}
    return entry


@pytest.fixture
def mock_hass():
    hass = MagicMock(spec=HomeAssistant)
    hass.config_entries = MagicMock()
    from unittest.mock import AsyncMock
    async def fake_update_entry(entry, options):
        entry.options.clear()
        entry.options.update(options)
    hass.config_entries.async_update_entry = AsyncMock(side_effect=fake_update_entry)
    return hass


@pytest.mark.asyncio
async def test_async_setup_entry(mock_hass, mock_entry):
    """Test the switch setup creates the correct entities."""
    async_add_entities = MagicMock()

    await async_setup_entry(mock_hass, mock_entry, async_add_entities)

    async_add_entities.assert_called_once()
    entities_added = async_add_entities.call_args[0][0]
    assert len(entities_added) == 4
    assert any(isinstance(e, SolarMaintenanceSwitch) for e in entities_added)
    assert any(isinstance(e, SolarDebugSwitch) for e in entities_added)
    assert any(isinstance(e, SolarScenarioBSwitch) for e in entities_added)
    assert any(isinstance(e, SolarScenarioCSwitch) for e in entities_added)


@pytest.mark.parametrize(
    "switch_class,expected_name,expected_unique_id,expected_icon",
    [
        (SolarMaintenanceSwitch, "Beschattungsautomatik pausieren", f"{DOMAIN}_automatic_paused", "mdi:pause-circle-outline"),
        (SolarDebugSwitch, "Debug Mode", f"{DOMAIN}_debug_mode", "mdi:bug"),
        (SolarScenarioBSwitch, "Scenario B Enabled", f"{DOMAIN}_scenario_b_enabled", "mdi:weather-cloudy"),
        (SolarScenarioCSwitch, "Scenario C Enabled", f"{DOMAIN}_scenario_c_enabled", "mdi:white-balance-sunny"),
    ],
)
def test_entity_attributes(switch_class, mock_hass, mock_entry, expected_name, expected_unique_id, expected_icon):
    """Test the attributes of the switch entities."""
    switch = switch_class(mock_hass, mock_entry)
    assert switch.name == expected_name
    assert switch.unique_id == expected_unique_id
    assert switch.icon == expected_icon
    assert switch.should_poll is False


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


@pytest.mark.parametrize(
    "switch_class,expected_default",
    [
        (SolarMaintenanceSwitch, False),
        (SolarDebugSwitch, False),
        (SolarScenarioBSwitch, True),
        (SolarScenarioCSwitch, True),
    ],
)
def test_switch_default_state(switch_class, mock_hass, mock_entry, expected_default):
    # Ensure options dict exists for all switches
    mock_entry.options = {}
    switch = switch_class(mock_hass, mock_entry)
    assert switch.is_on == expected_default


def test_switch_state_from_options(mock_hass, mock_entry):
    # Test SolarMaintenanceSwitch
    mock_entry.options = {"maintenance_mode": True}
    switch = SolarMaintenanceSwitch(mock_hass, mock_entry)
    assert switch.is_on is True

    mock_entry.options = {"maintenance_mode": False}
    switch = SolarMaintenanceSwitch(mock_hass, mock_entry)
    assert switch.is_on is False

    # Test SolarDebugSwitch
    mock_entry.options = {"debug_mode": True}
    switch = SolarDebugSwitch(mock_hass, mock_entry)
    assert switch.is_on is True

    mock_entry.options = {"debug_mode": False}
    switch = SolarDebugSwitch(mock_hass, mock_entry)
    assert switch.is_on is False

    # Test SolarScenarioBSwitch
    mock_entry.options = {"scenario_b_enabled": True}
    switch = SolarScenarioBSwitch(mock_hass, mock_entry)
    assert switch.is_on is True

    mock_entry.options = {"scenario_b_enabled": False}
    switch = SolarScenarioBSwitch(mock_hass, mock_entry)
    assert switch.is_on is False

    # Test SolarScenarioCSwitch
    mock_entry.options = {"scenario_c_enabled": True}
    switch = SolarScenarioCSwitch(mock_hass, mock_entry)
    assert switch.is_on is True

    mock_entry.options = {"scenario_c_enabled": False}
    switch = SolarScenarioCSwitch(mock_hass, mock_entry)
    assert switch.is_on is False


@pytest.mark.parametrize(
    "switch_class,key,initial_state",
    [
        (SolarMaintenanceSwitch, "maintenance_mode", True),
        (SolarDebugSwitch, "debug_mode", False),
        (SolarScenarioBSwitch, "scenario_b_enabled", True),
        (SolarScenarioCSwitch, "scenario_c_enabled", False),
    ],
)
async def test_switch_restore_state(switch_class, mock_hass, mock_entry, key, initial_state):
    """Test that the switch state is correctly restored after a simulated restart."""
    # Set an initial state in options
    mock_entry.options = {key: initial_state}

    # Simulate Home Assistant restart by re-initializing the switch
    switch = switch_class(mock_hass, mock_entry)

    # Assert that the switch's is_on property reflects the restored state
    assert switch.is_on == initial_state


@pytest.mark.parametrize(
    "switch_class,key",
    [
        (SolarMaintenanceSwitch, "maintenance_mode"),
        (SolarDebugSwitch, "debug_mode"),
        (SolarScenarioBSwitch, "scenario_b_enabled"),
        (SolarScenarioCSwitch, "scenario_c_enabled"),
    ],
)
async def test_switch_multiple_toggles(switch_class, mock_hass, mock_entry, key):
    """Test that multiple toggles do not cause side effects and state is consistent."""
    mock_entry.options = {key: False}  # Start with switch off
    switch = switch_class(mock_hass, mock_entry)
    mock_hass.async_add_job = lambda func, *args, **kwargs: func(*args, **kwargs)

    

    # Perform multiple toggles
    for i in range(5):
        # Turn on
        await switch.async_turn_on()
        assert switch.is_on is True
        mock_hass.config_entries.async_update_entry.assert_called_with(mock_entry, options={key: True})
        mock_hass.config_entries.async_update_entry.reset_mock()

        # Turn off
        await switch.async_turn_off()
        assert switch.is_on is False
        mock_hass.config_entries.async_update_entry.assert_called_with(mock_entry, options={key: False})
        mock_hass.config_entries.async_update_entry.reset_mock()

    # Ensure no extra calls to async_update_entry beyond the toggles
    mock_hass.config_entries.async_update_entry.assert_not_called()