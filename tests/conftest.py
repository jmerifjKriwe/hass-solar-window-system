"""Global fixtures and shared test data for the solar_window_system integration."""


import pytest
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN

# -------------------------------------------------------------------
# Shared constants
# -------------------------------------------------------------------

VALID_GLOBAL_INPUT = {
    "solar_radiation_sensor": "sensor.dummy_solar_radiation",
    "outdoor_temperature_sensor": "sensor.dummy_outdoor_temp",
    "update_interval": 5,
    "min_solar_radiation": 50,
    "min_sun_elevation": 10,
}

VALID_GLOBAL_THRESHOLDS = {
    "g_value": 0.3,
    "frame_width": 0.1,
    "tilt": 90,
    "diffuse_factor": 0.15,
    "threshold_direct": 200,
    "threshold_diffuse": 150,
    "indoor_base": 23.0,
    "outdoor_base": 19.5,
}

VALID_GLOBAL_OPTIONS = {
    "update_interval": 10,
    "min_solar_radiation": 80,
    "min_sun_elevation": 20,
}

VALID_WINDOW_INPUT = {
    "name": "Test Window South",
    "azimuth": 180,
    "width": 1.5,
    "height": 1.2,
    "azimuth_min": -45,
    "azimuth_max": 45,
    "elevation_min": 0,
    "elevation_max": 90,
    "shadow_depth": 0.5,
    "shadow_offset": 0.2,
    "room_temp_entity": "sensor.dummy_indoor_temp",
    "tilt": 90,
    "g_value": 0.7,
    "frame_width": 0.1,
}

VALID_WINDOW_OPTIONS = {
    "shading_mode": "manual",
    "indoor_temperature_sensor": "sensor.dummy_indoor_temp_group",
    "hvac_entity": "climate.living_room",
    "window_cover_entity": "cover.living_room_window",
}

# -------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in the test directory."""
    return


@pytest.fixture
def valid_global_input():
    return VALID_GLOBAL_INPUT


@pytest.fixture
def valid_thresholds():
    return VALID_GLOBAL_THRESHOLDS


@pytest.fixture
def valid_global_options():
    return VALID_GLOBAL_OPTIONS


@pytest.fixture
def valid_window_input():
    return VALID_WINDOW_INPUT


@pytest.fixture
def valid_window_options():
    return VALID_WINDOW_OPTIONS


@pytest.fixture
def mock_global_config_entry(valid_global_options) -> MockConfigEntry:
    """Return a mocked global config entry with options."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={"entry_type": "global"},
        options=valid_global_options,
        title="Global Solar Window System Config",
    )


@pytest.fixture
def mock_window_config_entry(valid_window_options) -> MockConfigEntry:
    """Return a mocked window config entry with options."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={"entry_type": "window"},
        options=valid_window_options,
        title="Test Window South",
    )


@pytest.fixture
async def setup_integration(
    hass: HomeAssistant,
    mock_global_config_entry: MockConfigEntry,
    mock_window_config_entry: MockConfigEntry,
):
    """Set up the integration for testing by registering config entries and dummy entities."""
    hass.states.async_set("sensor.dummy_solar_radiation", "800")
    hass.states.async_set("sensor.dummy_outdoor_temp", "20")
    hass.states.async_set("sensor.dummy_forecast_temp", "25")
    hass.states.async_set("sensor.dummy_indoor_temp", "24")
    hass.states.async_set("sensor.dummy_indoor_temp_group", "23")
    hass.states.async_set("binary_sensor.dummy_weather_warning", "off")
    hass.states.async_set("climate.office", "heat")
    hass.states.async_set("climate.living_room", "cool")
    hass.states.async_set("cover.office_window", "closed")
    hass.states.async_set("cover.living_room_window", "open")

    mock_global_config_entry.add_to_hass(hass)
    mock_window_config_entry.add_to_hass(hass)

    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

    yield mock_global_config_entry, mock_window_config_entry

    await hass.config_entries.async_unload(mock_global_config_entry.entry_id)
    await hass.config_entries.async_unload(mock_window_config_entry.entry_id)
    await hass.async_block_till_done()


@pytest.fixture
async def create_window_entry(
    hass: HomeAssistant, valid_window_input, valid_global_input
):
    """Create a window config entry for testing."""
    # First create a global entry to allow window entries
    global_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "entry_type": "global",
            **valid_global_input,
        },
        title="Global Config",
    )
    global_entry.add_to_hass(hass)

    # Then create the window entry
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "entry_type": "window",
            **valid_window_input,
        },
        title=valid_window_input["name"],  # Changed from window_name to name
    )
    entry.add_to_hass(hass)
    return entry
