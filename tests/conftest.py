"""Global fixtures for solar_window_system integration."""
import os
import shutil
import yaml
import pytest
from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN
from tests.mocks import MOCK_USER_INPUT, MOCK_OPTIONS, MOCK_CONFIG


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in the test."""
    yield


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_USER_INPUT,
        options=MOCK_OPTIONS,
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
    hass.states.async_set("sensor.dummy_indoor_temp_direct", "24")
    hass.states.async_set("sensor.dummy_indoor_temp_children", "21")
    hass.states.async_set("sensor.dummy_indoor_temp_bad_group", "22")

    mock_config_entry.add_to_hass(hass)

    solar_windows_path = hass.config.path("solar_windows")
    os.makedirs(solar_windows_path, exist_ok=True)

    try:
        with open(os.path.join(solar_windows_path, "windows.yaml"), "w") as f:
            yaml.dump({"windows": MOCK_CONFIG["windows"]}, f)

        with open(os.path.join(solar_windows_path, "groups.yaml"), "w") as f:
            yaml.dump({"groups": MOCK_CONFIG["groups"]}, f)

        # Setup the component
        assert await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()

        yield mock_config_entry

    finally:
        # Cleanup the created config files
        if os.path.exists(solar_windows_path):
            shutil.rmtree(solar_windows_path)