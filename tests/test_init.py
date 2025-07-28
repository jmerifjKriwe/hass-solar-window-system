import pytest
from unittest.mock import patch
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.solar_window_system.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState


@pytest.mark.asyncio
async def test_successful_setup(hass: HomeAssistant) -> None:
    """Test, ob die Integration korrekt eingerichtet und geladen wird."""

    # Patch hass.config.path so, dass der richtige config-Ordner zurückgegeben wird
    with patch.object(
        hass.config,
        "path",
        return_value="/workspaces/hass-solar-window-system/config/solar_windows",
    ):
        # 1. Setup der Abhängigkeiten: sun, input_number, template
        assert await async_setup_component(hass, "sun", {})
        assert await async_setup_component(hass, "input_number", {})
        assert await async_setup_component(hass, "template", {})

        # 2. Erstelle die input_number Helfer für Solarstrahlung und Außentemperatur
        await async_setup_component(
            hass,
            "input_number",
            {
                "input_number": {
                    "dummy_solar_radiation": {"min": 0, "max": 1200, "initial": 650},
                    "dummy_outdoor_temperature": {"min": -20, "max": 40, "initial": 17},
                }
            },
        )

        # 3. Erstelle Template-Sensoren für Solarstrahlung und Außentemperatur
        await async_setup_component(
            hass,
            "template",
            {
                "template": [
                    {
                        "sensor": {
                            "name": "Dummy Solar Radiation Sensor",
                            "unique_id": "dummy_solar_radiation_sensor",
                            "state": "{{ states('input_number.dummy_solar_radiation') }}",
                        }
                    },
                    {
                        "sensor": {
                            "name": "Dummy Outdoor Temperature Sensor",
                            "unique_id": "dummy_outdoor_temperature_sensor",
                            "state": "{{ states('input_number.dummy_outdoor_temperature') }}",
                            "device_class": "temperature",
                        }
                    },
                ]
            },
        )

        # 4. Erstelle dummy Template-Sensoren für Raumtemperaturen (21 Stück)
        for i in range(21):
            await async_setup_component(
                hass,
                "input_number",
                {
                    "input_number": {
                        f"dummy_temp_room_{i}": {"min": 15, "max": 30, "initial": 22}
                    }
                },
            )
            await async_setup_component(
                hass,
                "template",
                {
                    "template": [
                        {
                            "sensor": {
                                "name": f"Dummy Temperatur Raum {i}",
                                "unique_id": f"dummy_temperatur_raum_{i}",
                                "state": f"{{{{ states('input_number.dummy_temp_room_{i}') }}}}",
                            }
                        }
                    ]
                },
            )

        await hass.async_block_till_done()

        # 5. Erstelle einen Mock Config Entry mit nötigen Daten
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "solar_radiation_sensor": "sensor.dummy_solar_radiation_sensor",
                "outdoor_temperature_sensor": "sensor.dummy_outdoor_temperature_sensor",
            },
        )
        entry.add_to_hass(hass)

        # 6. Patch das Laden der YAML-Dateien, falls nötig
        mock_config_data = {
            "defaults": {"temperatures": {"indoor_base": 21, "outdoor_base": 16}},
            "groups": {},
            "windows": {
                f"window_{i}": {
                    "name": f"Window {i}",
                    "room_temp_entity": f"sensor.dummy_temperatur_raum_{i}",
                }
                for i in range(21)
            },
        }

        with patch(
            "custom_components.solar_window_system.__init__._load_config_from_files",
            return_value=mock_config_data,
        ):
            # 7. Setup der Integration via Config Entry
            await hass.config_entries.async_setup(entry.entry_id)
            await hass.async_block_till_done()

        # 8. Prüfe, ob der Eintrag geladen ist
        assert entry.state is ConfigEntryState.LOADED

        # 9. Prüfe, ob der Coordinator im hass.data ist
        coordinator = hass.data[DOMAIN][entry.entry_id]
        assert coordinator is not None
        assert hasattr(coordinator, "data")
        assert coordinator.data is not None
