"""Global fixtures for solar_window_system integration."""

import pytest
from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry


from custom_components.solar_window_system.const import DOMAIN, CONF_ENTRY_TYPE
from tests.mocks import MOCK_GLOBAL_INPUT, MOCK_WINDOW_INPUT, MOCK_GROUP_INPUT


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in the test."""
    yield


@pytest.fixture
def mock_global_config_entry() -> MockConfigEntry:
    """Return a mocked global config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_ENTRY_TYPE: "global"},
        options=MOCK_GLOBAL_INPUT,
        title="Global Solar Window System Config",
    )


@pytest.fixture
def mock_window_config_entry() -> MockConfigEntry:
    """Return a mocked window config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_ENTRY_TYPE: "window"},
        options=MOCK_WINDOW_INPUT,
        title="Test Window South",
    )


@pytest.fixture
async def setup_integration(
    hass: HomeAssistant,
    mock_global_config_entry: MockConfigEntry,
    mock_window_config_entry: MockConfigEntry,
):
    """Set up the integration for testing by creating dummy config files and entities."""
    # Set up dummy entities that the integration depends on
    hass.states.async_set("sensor.dummy_solar_radiation", "800")
    hass.states.async_set("sensor.dummy_outdoor_temp", "20")
    hass.states.async_set("sensor.dummy_forecast_temp", "25")
    hass.states.async_set("sensor.dummy_indoor_temp", "24")
    hass.states.async_set("sensor.dummy_indoor_temp_group", "23")
    hass.states.async_set("binary_sensor.dummy_weather_warning", "off")

    # Add config entries to Home Assistant
    mock_global_config_entry.add_to_hass(hass)
    mock_window_config_entry.add_to_hass(hass)

    # Setup the component
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    yield mock_global_config_entry, mock_window_config_entry

    # Clean up after test
    await hass.config_entries.async_unload(mock_global_config_entry.entry_id)
    await hass.config_entries.async_unload(mock_window_config_entry.entry_id)
    await hass.async_block_till_done()
