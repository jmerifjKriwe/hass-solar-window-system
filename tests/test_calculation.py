import pytest
import yaml
import logging
from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN
from .mocks import MOCK_CONFIG, MOCK_USER_INPUT, MOCK_OPTIONS


async def setup_integration(
    hass: HomeAssistant, solar_radiation: str, test_id: str, tmp_path
):
    """Richtet die Integration und alle abhängigen Mock-Sensoren korrekt ein."""
    config_dir = tmp_path / "solar_windows"
    config_dir.mkdir()
    with open(config_dir / "windows.yaml", "w") as f:
        yaml.dump({"windows": MOCK_CONFIG["windows"]}, f)
    with open(config_dir / "groups.yaml", "w") as f:
        yaml.dump({"groups": {}}, f)

    # Lade die Abhängigkeiten
    assert await async_setup_component(hass, "sun", {})
    assert await async_setup_component(hass, "input_number", {})
    assert await async_setup_component(hass, "template", {})

    # Setze die Zustände der Sensoren direkt.
    hass.states.async_set("sun.sun", "above_horizon", {"elevation": 45, "azimuth": 170})
    hass.states.async_set("sensor.dummy_solar_radiation", solar_radiation)
    hass.states.async_set("sensor.dummy_outdoor_temp", "22.0")
    hass.states.async_set("sensor.dummy_indoor_temp", "24.0")
    await hass.async_block_till_done()

    # Erstelle einen Mock-Config-Eintrag.
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_USER_INPUT,
        options=MOCK_OPTIONS,
        entry_id=f"test_entry_{test_id}",
    )
    entry.add_to_hass(hass)

    # Patche hass.config.path und führe das Setup aus.
    with patch.object(
        hass.config, "path", side_effect=lambda *args: str(tmp_path.joinpath(*args))
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return entry


@pytest.mark.parametrize(
    ("solar_radiation", "expected_state", "expected_power", "expected_reason_part"),
    [
        ("800", STATE_ON, 1206.8, "Strong sun"),
        ("50", STATE_OFF, 75.4, "No shading required"),
    ],
)
@pytest.mark.asyncio
async def test_shading_calculation(
    hass: HomeAssistant,
    solar_radiation: str,
    expected_state: str,
    expected_power: float,
    expected_reason_part: str,
    tmp_path,
):
    """Testet die Verschattungslogik und validiert die Berechnungsergebnisse."""
    # Erstelle eine eindeutige ID für den Testlauf, um Konflikte zu vermeiden
    unique_test_id = f"test_{solar_radiation}"
    await setup_integration(hass, solar_radiation, unique_test_id, tmp_path)

    entity_id = "binary_sensor.solar_window_system_test_window_south_shading"
    state = hass.states.get(entity_id)

    # Prüfung 1: Wurde der Sensor erstellt und hat er den korrekten Zustand?
    assert state is not None, f"Der Shading-Sensor '{entity_id}' wurde nicht erzeugt."
    assert state.state == expected_state, (
        f"Erwarteter Zustand war '{expected_state}', aber der Zustand ist '{state.state}'."
    )

    # Prüfung 2: Wurde die Leistung korrekt berechnet?
    # Wir prüfen, ob der berechnete Wert nahe am theoretischen Wert liegt.
    calculated_power = state.attributes.get("power_total_w")
    assert calculated_power == pytest.approx(expected_power, rel=0.01), (
        f"Die berechnete Leistung ({calculated_power}W) weicht zu stark von der erwarteten Leistung ({expected_power}W) ab."
    )

    # Prüfung 3: Ist der Grund für die Entscheidung korrekt?
    reason = state.attributes.get("reason")
    # Stelle sicher, dass 'reason' ein String ist, bevor der 'in'-Operator verwendet wird.
    assert isinstance(reason, str), (
        f"Das 'reason'-Attribut ist kein String, sondern: {type(reason)}"
    )
    assert expected_reason_part in reason, (
        f"Der erwartete Grund '{expected_reason_part}' wurde in der Begründung '{reason}' nicht gefunden."
    )
