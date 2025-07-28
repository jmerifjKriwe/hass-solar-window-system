# tests/test_smoke.py
"""Smoke tests for the Solar Window System integration."""

import pytest
import logging
import yaml
from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntryState
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN
from .mocks import MOCK_CONFIG, MOCK_USER_INPUT


@pytest.mark.asyncio
async def test_load_unload_with_real_files(hass: HomeAssistant, tmp_path, caplog):
    """Test that the integration can be set up and unloaded successfully using real YAML files."""

    caplog.set_level(logging.DEBUG)

    # 1. Erstelle die notwendige Verzeichnisstruktur und Konfigurationsdateien.
    config_dir = tmp_path / "solar_windows"
    config_dir.mkdir()
    with open(config_dir / "windows.yaml", "w") as f:
        yaml.dump({"windows": MOCK_CONFIG["windows"]}, f)
    with open(config_dir / "groups.yaml", "w") as f:
        yaml.dump({"groups": {}}, f)

    # 2. Lade ALLE Abhängigkeiten aus manifest.json.
    assert await async_setup_component(hass, "sun", {})
    assert await async_setup_component(hass, "input_number", {})
    assert await async_setup_component(hass, "template", {})

    # Erstelle die Template-Sensoren, die in MOCK_USER_INPUT referenziert werden.
    assert await async_setup_component(
        hass,
        "sensor",
        {
            "sensor": [
                {
                    "platform": "template",
                    "sensors": {
                        "dummy_solar_radiation": {"value_template": "{{ 100 }}"},
                        "dummy_outdoor_temp": {"value_template": "{{ 20 }}"},
                        "dummy_indoor_temp": {"value_template": "{{ 22 }}"},
                    },
                }
            ]
        },
    )
    await hass.async_block_till_done()

    # 3. Erstelle einen Mock-Config-Eintrag für die Integration.
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_USER_INPUT,
        entry_id="test_smoke_entry",
    )
    entry.add_to_hass(hass)

    # 4. Patche hass.config.path, um auf tmp_path/solar_windows zuzugreifen
    with patch.object(
        hass.config, "path", side_effect=lambda *args: str(tmp_path.joinpath(*args))
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    # 5. Prüfung: War das Setup erfolgreich?
    if entry.state != ConfigEntryState.LOADED:
        print("\n--- DEBUG LOG OUTPUT ---")
        for record in caplog.records:
            print(f"{record.levelname}: {record.getMessage()}")

    assert entry.state is ConfigEntryState.LOADED, (
        f"Integration failed to load, state is {entry.state}"
    )

    # 6. Unload und abschließende Prüfung
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
