"""Globale Fixtures für Tests der Solar Window System Integration."""

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

# Integration-Domain (muss mit dem tatsächlichen Verzeichnisnamen übereinstimmen)
DOMAIN = "solar_window_system"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Erlaube die Verwendung von benutzerdefinierten Integrationen im Testverzeichnis."""
    yield


@pytest.fixture
def mock_config_entry():
    """Gibt ein MockConfigEntry-Objekt zurück."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "solar_radiation_sensor": "sensor.dummy_solar_radiation",
            "outdoor_temperature_sensor": "sensor.dummy_outdoor_temp",
        },
        unique_id="test_unique_id",
        options={},
    )


@pytest.fixture
async def setup_integration(hass: HomeAssistant, mock_config_entry):
    """Setzt die Integration vollständig auf."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry
