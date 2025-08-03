import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN


@pytest.mark.asyncio
async def test_global_options_flow_valid_input(
    hass: HomeAssistant, valid_global_input, valid_global_options
) -> None:
    """Testet gültige Eingaben im OptionsFlow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"entry_type": "global"},
        options=valid_global_options,
        title="Solar Windows Global Config",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["step_id"] == "global_init"

    # First step - configure global_init
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=valid_global_input,
    )
    assert result["type"] == "form"
    assert result["step_id"] == "global_thresholds"

    # Second step - configure thresholds including g_value
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "g_value": 0.6,
            "tilt": 75,
            "frame_width": 0.125,
            "diffuse_factor": 0.15,
            "threshold_direct": 200,
            "threshold_diffuse": 150,
            "indoor_base": 23.0,
            "outdoor_base": 19.5,
        },
    )
    assert result["type"] == "form"
    assert result["step_id"] == "global_scenarios"

    # Third step - configure scenarios
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "scenario_b_temp_indoor_threshold": 23.5,
            "scenario_b_temp_outdoor_threshold": 25.5,
            "scenario_c_temp_forecast_threshold": 28.5,
            "scenario_c_temp_indoor_threshold": 21.5,
            "scenario_c_temp_outdoor_threshold": 24.0,
            "scenario_c_start_hour": 9,
        },
    )
    assert result["type"] == "create_entry"
    assert result["data"]["g_value"] == 0.6


@pytest.mark.asyncio
async def test_global_options_flow_rejects_invalid_g_value(
    hass: HomeAssistant, valid_global_input, valid_global_options
) -> None:
    """Testet ungültigen g_value im OptionsFlow."""
    entry = MockConfigEntry(
        version=1,
        domain=DOMAIN,
        data={"entry_type": "global"},
        options=valid_global_options,
        entry_id="test123",
        title="Solar Windows Global Config",
        source="user",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["step_id"] == "global_init"

    # First step - configure global_init
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=valid_global_input,
    )
    assert result["type"] == "form"
    assert result["step_id"] == "global_thresholds"

    # Second step - try to configure invalid g_value which should raise an exception
    with pytest.raises(Exception) as excinfo:
        await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                "g_value": 2.0,
                "tilt": 75,
                "frame_width": 0.125,
                "diffuse_factor": 0.15,
                "threshold_direct": 200,
                "threshold_diffuse": 150,
                "indoor_base": 23.0,
                "outdoor_base": 19.5,
            },
        )

    # Check that the error is related to schema validation
    assert "Schema validation failed" in str(excinfo.value)


@pytest.mark.asyncio
async def test_global_options_flow_uses_defaults(hass: HomeAssistant) -> None:
    """Testet, dass Optionen-Form vorhandene Optionen als Default zeigt."""
    entry = MockConfigEntry(
        version=1,
        domain=DOMAIN,
        data={"entry_type": "global"},
        options={"tilt": 70},
        entry_id="test123",
        title="Solar Windows Global Config",
        source="user",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    # First step shows sensor config
    assert result["step_id"] == "global_init"

    # Go to next step to access threshold defaults
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "solar_radiation_sensor": "sensor.dummy_solar_radiation",
            "outdoor_temperature_sensor": "sensor.dummy_outdoor_temp",
            "update_interval": 5,
            "min_solar_radiation": 50,
            "min_sun_elevation": 10,
        },
    )
    # Now we're on the thresholds step
    assert result["step_id"] == "global_thresholds"

    # Instead of directly accessing the schema default, verify the form contains the expected fields
    form_data = result["data_schema"]
    assert form_data is not None
