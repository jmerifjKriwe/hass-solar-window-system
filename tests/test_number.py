import pytest
from unittest.mock import MagicMock
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from custom_components.solar_window_system.number import (
    SolarGlobalSensitivityNumber,
    SolarChildrenFactorNumber,
    SolarTemperatureOffsetNumber,
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


def test_number_native_value_and_set(mock_hass, mock_entry):
    import asyncio

    # Global Sensitivity
    number = SolarGlobalSensitivityNumber(mock_hass, mock_entry)
    assert isinstance(number.native_value, float)
    asyncio.run(number.async_set_native_value(0.7))
    assert number.native_value == 0.7
    # Children Factor
    number = SolarChildrenFactorNumber(mock_hass, mock_entry)
    asyncio.run(number.async_set_native_value(1.2))
    assert number.native_value == 1.2
    # Temperature Offset
    number = SolarTemperatureOffsetNumber(mock_hass, mock_entry)
    asyncio.run(number.async_set_native_value(-2.0))
    assert number.native_value == -2.0
