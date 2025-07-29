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


@pytest.mark.parametrize(
    "preset,expected_sensitivity,expected_children_factor",
    [
        ("Normal", 1.0, 0.8),
        ("Relaxed", 0.7, 1.2),
        ("Sensitive", 1.5, 0.5),
        ("Children", 1.0, 0.3),
    ],
)
def test_preset_sets_options_correctly(
    mock_hass, mock_entry, preset, expected_sensitivity, expected_children_factor
):
    mock_entry.options = {}
    select = SolarPresetSelect(mock_hass, mock_entry)

    # Patch async_update_entry to just update the entry.options dict
    def fake_update_entry(entry, options):
        entry.options.clear()
        entry.options.update(options)

    mock_hass.config_entries.async_update_entry.side_effect = fake_update_entry

    import asyncio

    asyncio.run(select.async_select_option(preset))

    assert mock_entry.options["preset_mode"] == preset
    assert mock_entry.options["global_sensitivity"] == expected_sensitivity
    assert mock_entry.options["children_factor"] == expected_children_factor


def test_custom_values_return_custom_option(mock_hass, mock_entry):
    """Test that non-preset values result in 'Custom' as current_option."""
    # Werte, die keinem Preset entsprechen
    mock_entry.options = {
        "global_sensitivity": 1.23,
        "children_factor": 0.42,
    }
    select = SolarPresetSelect(mock_hass, mock_entry)
    assert select.current_option == "Custom"


def test_invalid_option_does_not_change_options(mock_hass, mock_entry):
    """Test that an invalid option for async_select_option does not change options or raises an Exception."""
    mock_entry.options = {"global_sensitivity": 1.0, "children_factor": 0.8}
    select = SolarPresetSelect(mock_hass, mock_entry)

    # Patch async_update_entry to just update the entry.options dict
    def fake_update_entry(entry, options):
        entry.options.clear()
        entry.options.update(options)

    mock_hass.config_entries.async_update_entry.side_effect = fake_update_entry

    import asyncio

    # Save original state
    original_options = dict(mock_entry.options)
    # Try invalid option
    with pytest.raises(Exception):
        asyncio.run(select.async_select_option("INVALID"))
    # Optionally, check that options did not change
    assert mock_entry.options == original_options
