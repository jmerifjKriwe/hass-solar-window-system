"""Global fixtures for solar_window_system integration."""
import pytest
from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN
from tests.mocks import MOCK_USER_INPUT, MOCK_WINDOW_INPUT, MOCK_GROUP_INPUT


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in the test."""
    yield


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={},
        options=MOCK_USER_INPUT,
    )


@pytest.fixture
async def setup_integration(hass: HomeAssistant, mock_config_entry: MockConfigEntry):
    """Set up the integration for testing by creating dummy config files and entities."""
    # Set up dummy entities that the integration depends on
    hass.states.async_set("sensor.dummy_solar_radiation", "800")
    hass.states.async_set("sensor.dummy_outdoor_temp", "20")
    hass.states.async_set("sensor.dummy_forecast_temp", "25")
    hass.states.async_set("sensor.dummy_indoor_temp", "24")
    hass.states.async_set("sensor.dummy_indoor_temp_group", "23")
    hass.states.async_set("binary_sensor.dummy_weather_warning", "off")

    # Create mock sub-entries
    window_entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_WINDOW_INPUT,
        title="Test Window South",
    )
    window_entry.parent_entry_id = mock_config_entry.entry_id
    window_entry.add_to_hass(hass)

    group_entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_GROUP_INPUT,
        title="Test Group",
    )
    group_entry.parent_entry_id = mock_config_entry.entry_id
    group_entry.add_to_hass(hass)

    mock_config_entry.add_to_hass(hass)

    # Setup the component
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    yield mock_config_entry
