import pytest
from unittest.mock import MagicMock
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from custom_components.solar_window_system.select import SolarPresetSelect


@pytest.fixture
def mock_entry():
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    return entry


@pytest.fixture
def mock_hass():
    return MagicMock(spec=HomeAssistant)


def test_select_option_and_current(mock_hass, mock_entry):
    # Provide options attribute for the mock entry
    mock_entry.options = {}
    select = SolarPresetSelect(mock_hass, mock_entry)
    # Default option
    assert select.current_option in select.options
    # Set new option
    import asyncio

    new_option = select.options[0]
    asyncio.run(select.async_select_option(new_option))
    assert select.current_option == new_option
