import pytest
from unittest.mock import patch
from pytest_homeassistant_custom_component.common import MockConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.solar_window_system.const import DOMAIN

from tests.mocks import MOCK_USER_INPUT, MOCK_OPTIONS, MOCK_CONFIG


@pytest.mark.asyncio
async def test_default_values_present(hass: HomeAssistant) -> None:
    """Testet, ob beim Setup die Default-Werte aus der Config geladen werden."""

    # Mock ConfigEntry erstellen und zu Home Assistant hinzufügen
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_INPUT, options=MOCK_OPTIONS)
    entry.add_to_hass(hass)

    # Patchen, damit statt Laden aus Dateien unser MOCK_CONFIG verwendet wird
    with patch(
        "custom_components.solar_window_system._load_config_from_files",
        return_value=MOCK_CONFIG,
    ):
        # Setup des ConfigEntries (Initialisierung des Components)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    # Zugriff auf den Coordinator (der die Daten hält)
    coordinator = hass.data[DOMAIN][entry.entry_id]

    print(coordinator.data)

    # Defaults aus dem Coordinator holen
    defaults = coordinator.defaults

    # Prüfungen: Sind die Defaults wie erwartet gesetzt?
    assert "physical" in defaults
    assert defaults["physical"]["g_value"] == 0.5
    assert defaults["physical"]["frame_width"] == 0.125
    assert defaults["thresholds"]["direct"] == 200
    assert defaults["temperatures"]["indoor_base"] == 23.0

    # Beispiel: Prüfen, dass Szenario B aktiviert ist
    assert defaults["scenario_b"]["enabled"] is True

    # Beispiel: Prüfen, dass minimaler Sonnenstand gesetzt ist
    assert defaults["calculation"]["min_sun_elevation"] == 10
