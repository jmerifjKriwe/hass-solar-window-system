import pytest
from unittest.mock import MagicMock
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from custom_components.solar_window_system.select import SolarPresetSelect, async_setup_entry, PRESET_OPTIONS
from custom_components.solar_window_system.const import DOMAIN
from custom_components.solar_window_system.number import SolarGlobalSensitivityNumber


@pytest.fixture
def mock_entry():
    """Fixture for a mock config entry."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.options = {}
    return entry


@pytest.fixture
def mock_hass():
    """Fixture for a mock Home Assistant."""
    hass = MagicMock(spec=HomeAssistant)
    hass.config_entries = MagicMock()

    def fake_update_entry(entry, options):
        """Fake implementation of async_update_entry."""
        entry.options.clear()
        entry.options.update(options)

    hass.config_entries.async_update_entry.side_effect = fake_update_entry
    return hass


@pytest.mark.asyncio
async def test_async_setup_entry(mock_hass, mock_entry):
    """Test the select setup creates the correct entity."""
    async_add_entities = MagicMock()

    await async_setup_entry(mock_hass, mock_entry, async_add_entities)

    async_add_entities.assert_called_once()
    entities_added = async_add_entities.call_args[0][0]
    assert len(entities_added) == 1
    assert isinstance(entities_added[0], SolarPresetSelect)


def test_entity_attributes(mock_hass, mock_entry):
    """Test the attributes of the SolarPresetSelect entity."""
    select = SolarPresetSelect(mock_hass, mock_entry)
    assert select.name == "Preset Mode"
    assert select.unique_id == f"{DOMAIN}_preset_mode"
    assert select.icon == "mdi:tune"
    assert select.options == PRESET_OPTIONS


def test_select_option_and_current(mock_hass, mock_entry):
    # Provide options attribute for the mock entry
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
    select = SolarPresetSelect(mock_hass, mock_entry)

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

    import asyncio

    # Save original state
    original_options = dict(mock_entry.options)
    # Try invalid option
    with pytest.raises(Exception):
        asyncio.run(select.async_select_option("INVALID"))
    # Optionally, check that options did not change
    assert mock_entry.options == original_options


def test_children_preset_sets_sensitivity_to_default(mock_hass, mock_entry):
    """Test that selecting the 'Children' preset sets a default sensitivity."""
    mock_entry.options = {"global_sensitivity": 1.5}  # Start with a non-default value
    select = SolarPresetSelect(mock_hass, mock_entry)

    import asyncio

    asyncio.run(select.async_select_option("Children"))

    assert mock_entry.options["global_sensitivity"] == 1.0
    assert mock_entry.options["children_factor"] == 0.3


def test_current_option_is_custom_when_not_matching_preset(mock_hass, mock_entry):
    """Test that current_option is 'Custom' if values don't match any preset."""
    mock_entry.options = {
        "global_sensitivity": 0.9,  # Not a preset value
        "children_factor": 0.8,
    }
    select = SolarPresetSelect(mock_hass, mock_entry)
    assert select.current_option == "Custom"

    mock_entry.options = {
        "global_sensitivity": 1.0,
        "children_factor": 0.9,  # Not a preset value
    }
    select = SolarPresetSelect(mock_hass, mock_entry)
    assert select.current_option == "Custom"


def test_current_option_matches_preset(mock_hass, mock_entry):
    """Test that current_option correctly identifies a preset."""
    mock_entry.options = {"global_sensitivity": 0.7, "children_factor": 1.2}
    select = SolarPresetSelect(mock_hass, mock_entry)
    assert select.current_option == "Relaxed"

    mock_entry.options = {"global_sensitivity": 1.5, "children_factor": 0.5}
    select = SolarPresetSelect(mock_hass, mock_entry)
    assert select.current_option == "Sensitive"

    mock_entry.options = {"global_sensitivity": 1.0, "children_factor": 0.8}
    select = SolarPresetSelect(mock_hass, mock_entry)
    assert select.current_option == "Normal"

    mock_entry.options = {"global_sensitivity": 1.0, "children_factor": 0.3}
    select = SolarPresetSelect(mock_hass, mock_entry)
    assert select.current_option == "Children"


def test_relevant_number_change_sets_preset_to_custom(mock_hass, mock_entry):
    """Test that changing a relevant number entity sets the mode to Custom."""
    # Initial state: "Normal" preset
    mock_entry.options = {
        "preset_mode": "Normal",
        "global_sensitivity": 1.0,
        "children_factor": 0.8,
    }

    select_entity = SolarPresetSelect(mock_hass, mock_entry)
    number_entity = SolarGlobalSensitivityNumber(mock_hass, mock_entry)

    # Verify initial state
    assert select_entity.current_option == "Normal"

    # Change a relevant number entity value
    import asyncio

    asyncio.run(number_entity.async_set_native_value(1.5))

    # Verify preset is now "Custom"
    assert select_entity.current_option == "Custom"


def test_manual_custom_override(mock_hass, mock_entry):
    """Test that if preset_mode is 'Custom', it remains 'Custom' even if values match a preset."""
    # Values match "Normal", but preset_mode is "Custom"
    mock_entry.options = {
        "preset_mode": "Custom",
        "global_sensitivity": 1.0,
        "children_factor": 0.8,
    }
    select = SolarPresetSelect(mock_hass, mock_entry)
    assert select.current_option == "Custom"

    # Change to a preset
    import asyncio

    asyncio.run(select.async_select_option("Relaxed"))
    assert select.current_option == "Relaxed"

    # Manually change a value, which should implicitly set to Custom
    number_entity = SolarGlobalSensitivityNumber(mock_hass, mock_entry)
    asyncio.run(number_entity.async_set_native_value(1.1))
    assert select.current_option == "Custom"
