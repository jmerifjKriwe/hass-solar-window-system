import pytest
from unittest.mock import MagicMock, call
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from custom_components.solar_window_system.switch import (
    async_setup_entry,
    SolarMaintenanceSwitch,
    SolarDebugSwitch,
    SolarScenarioBSwitch,
    SolarScenarioCSwitch,
)


@pytest.fixture
def mock_entry():
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    # Simulate persistent options dict
    entry.options = {}
    return entry


@pytest.fixture
def mock_hass(mock_entry):
    hass = MagicMock(spec=HomeAssistant)

    # Patch config_entries.async_update_entry to update options dict
    def async_update_entry(entry, options=None):
        if options is not None:
            entry.options.update(options)

    hass.config_entries.async_update_entry.side_effect = async_update_entry
    return hass


@pytest.mark.asyncio
async def test_async_setup_entry(mock_hass, mock_entry):
    """Test the switch setup creates the correct entities."""
    async_add_entities = MagicMock()

    await async_setup_entry(mock_hass, mock_entry, async_add_entities)

    async_add_entities.assert_called_once()
    entities_added = async_add_entities.call_args[0][0]
    assert len(entities_added) == 4


@pytest.mark.parametrize(
    "switch_class,expected_name,expected_unique_id,expected_icon",
    [
        (SolarMaintenanceSwitch, "Beschattungsautomatik pausieren", "solar_window_system_automatic_paused", "mdi:pause-circle-outline"),
        (SolarDebugSwitch, "Debug Mode", "solar_window_system_debug_mode", "mdi:bug"),
        (SolarScenarioBSwitch, "Scenario B Enabled", "solar_window_system_scenario_b_enabled", "mdi:weather-cloudy"),
        (SolarScenarioCSwitch, "Scenario C Enabled", "solar_window_system_scenario_c_enabled", "mdi:white-balance-sunny"),
    ],
)
def test_entity_attributes(
    switch_class,
    expected_name,
    expected_unique_id,
    expected_icon,
    mock_hass,
    mock_entry,
):
    switch = switch_class(mock_hass, mock_entry)
    assert switch.name == expected_name
    assert switch.unique_id == expected_unique_id
    assert switch.icon == expected_icon


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
    import asyncio

    switch = switch_class(mock_hass, mock_entry)
    assert not switch.is_on

    asyncio.run(switch.async_turn_on())
    assert switch.is_on

    asyncio.run(switch.async_turn_off())
    assert not switch.is_on
