"""Test various scenarios for the solar_window_system component."""
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_ON, STATE_OFF

from .conftest import setup_integration


@pytest.mark.asyncio
async def test_all_power_attributes(hass: HomeAssistant, setup_integration):
    """Test that all attributes of the power sensor are calculated correctly."""
    hass.states.async_set("sun.sun", "above_horizon", {"elevation": 45, "azimuth": 170})
    hass.states.async_set("sensor.dummy_solar_radiation", "800")
    hass.states.async_set("sensor.dummy_outdoor_temp", "22.0")
    hass.states.async_set("sensor.dummy_indoor_temp", "24.0")
    await hass.async_block_till_done()

    coordinator = hass.data[setup_integration.domain][setup_integration.entry_id]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    entity_id = "sensor.solar_window_system_test_window_south_power"
    state = hass.states.get(entity_id)

    assert state is not None
    assert state.attributes.get("area_m2") == pytest.approx(3.0625)
    assert state.attributes.get("power_direct") == pytest.approx(1025.5, rel=0.01)
    assert state.attributes.get("power_diffuse") == pytest.approx(183.8, rel=0.01)
    assert float(state.state) == pytest.approx(1209.3, rel=0.01)


@pytest.mark.asyncio
async def test_group_override(hass: HomeAssistant, setup_integration):
    """Test that an override from groups.yaml is applied correctly."""
    hass.states.async_set("sun.sun", "above_horizon", {"elevation": 45, "azimuth": 170})
    hass.states.async_set("sensor.dummy_solar_radiation", "370")
    hass.states.async_set("sensor.dummy_outdoor_temp", "22.0")
    hass.states.async_set("sensor.dummy_indoor_temp_group", "24.0")
    await hass.async_block_till_done()

    coordinator = hass.data[setup_integration.domain][setup_integration.entry_id]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    entity_id = "binary_sensor.solar_window_system_test_window_group_override_shading"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_ON
    assert "Strong sun" in state.attributes.get("reason", "")


@pytest.mark.asyncio
async def test_window_override(hass: HomeAssistant, setup_integration):
    """Test that an override from windows.yaml is applied correctly."""
    hass.states.async_set("sun.sun", "above_horizon", {"elevation": 45, "azimuth": 170})
    hass.states.async_set("sensor.dummy_solar_radiation", "440")
    hass.states.async_set("sensor.dummy_outdoor_temp", "22.0")
    hass.states.async_set("sensor.dummy_indoor_temp_direct", "24.0")
    await hass.async_block_till_done()

    coordinator = hass.data[setup_integration.domain][setup_integration.entry_id]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    entity_id = "binary_sensor.solar_window_system_test_window_direct_override_shading"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_ON
    assert "Strong sun" in state.attributes.get("reason", "")


@pytest.mark.asyncio
async def test_scenario_b(hass: HomeAssistant, setup_integration):
    """Test that scenario B is triggered correctly."""
    hass.states.async_set("sun.sun", "above_horizon", {"elevation": 45, "azimuth": 170})
    hass.states.async_set("sensor.dummy_solar_radiation", "130")
    hass.states.async_set("sensor.dummy_outdoor_temp", "26.0")
    hass.states.async_set("sensor.dummy_indoor_temp", "24.0")
    await hass.async_block_till_done()

    coordinator = hass.data[setup_integration.domain][setup_integration.entry_id]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    entity_id = "binary_sensor.solar_window_system_test_window_south_shading"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_ON
    assert "Diffuse heat" in state.attributes.get("reason", "")


@pytest.mark.asyncio
async def test_scenario_c(hass: HomeAssistant, setup_integration, freezer):
    """Test that scenario C is triggered correctly."""
    freezer.move_to("2025-07-28 10:00:00")
    hass.states.async_set("sun.sun", "above_horizon", {"elevation": 45, "azimuth": 170})
    hass.states.async_set("sensor.dummy_solar_radiation", "100")
    hass.states.async_set("sensor.dummy_outdoor_temp", "22.0")
    hass.states.async_set("sensor.dummy_indoor_temp", "24.0")
    hass.states.async_set("sensor.dummy_forecast_temp", "30.0")
    await hass.async_block_till_done()

    coordinator = hass.data[setup_integration.domain][setup_integration.entry_id]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    entity_id = "binary_sensor.solar_window_system_test_window_south_shading"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_ON
    assert "Heatwave forecast" in state.attributes.get("reason", "")


@pytest.mark.asyncio
async def test_maintenance_mode(hass: HomeAssistant, setup_integration):
    """Test that no shading occurs in maintenance mode."""
    hass.config_entries.async_update_entry(
        setup_integration, options={"maintenance_mode": True}
    )
    await hass.async_block_till_done()

    coordinator = hass.data[setup_integration.domain][setup_integration.entry_id]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    entity_id = "binary_sensor.solar_window_system_test_window_south_shading"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_OFF
    assert "Maintenance mode" in state.attributes.get("reason", "")


@pytest.mark.asyncio
async def test_sun_not_visible(hass: HomeAssistant, setup_integration):
    """Test that no shading occurs (due to direct radiation) when the sun is not visible."""
    hass.states.async_set("sun.sun", "above_horizon", {"elevation": 45, "azimuth": 10})
    await hass.async_block_till_done()

    coordinator = hass.data[setup_integration.domain][setup_integration.entry_id]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    entity_id = "binary_sensor.solar_window_system_test_window_south_shading"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_OFF


@pytest.mark.asyncio
async def test_scenario_c_before_start_hour(hass: HomeAssistant, setup_integration, freezer):
    """Test that scenario C does not trigger before the start hour."""
    freezer.move_to("2025-07-28 08:00:00")
    # Set a low solar radiation to prevent scenario A from triggering
    hass.states.async_set("sensor.dummy_solar_radiation", "100")
    hass.states.async_set("sensor.dummy_forecast_temp", "30.0")
    await hass.async_block_till_done()

    coordinator = hass.data[setup_integration.domain][setup_integration.entry_id]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    entity_id = "binary_sensor.solar_window_system_test_window_south_shading"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_OFF


@pytest.mark.asyncio
async def test_weather_warning_override(hass: HomeAssistant, setup_integration):
    """Test that a weather warning forces shading."""
    hass.states.async_set("sensor.dummy_weather_warning", "on")
    hass.config_entries.async_update_entry(
        setup_integration, options={"weather_warning_sensor": "sensor.dummy_weather_warning"}
    )
    await hass.async_block_till_done()

    coordinator = hass.data[setup_integration.domain][setup_integration.entry_id]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    entity_id = "binary_sensor.solar_window_system_test_window_south_shading"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_ON
    assert "Weather warning" in state.attributes.get("reason", "")


@pytest.mark.asyncio
async def test_cold_day_no_shading(hass: HomeAssistant, setup_integration):
    """Test that no shading occurs on a cold but sunny day."""
    hass.states.async_set("sensor.dummy_outdoor_temp", "5.0")
    await hass.async_block_till_done()

    coordinator = hass.data[setup_integration.domain][setup_integration.entry_id]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    entity_id = "binary_sensor.solar_window_system_test_window_south_shading"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_OFF


@pytest.mark.asyncio
async def test_high_sensitivity_triggers_sooner(hass: HomeAssistant, setup_integration):
    """Test that a higher sensitivity triggers shading sooner."""
    hass.states.async_set("sensor.dummy_solar_radiation", "550")
    hass.config_entries.async_update_entry(
        setup_integration, options={**setup_integration.options, "global_sensitivity": 2.0}
    )
    await hass.async_block_till_done()

    coordinator = hass.data[setup_integration.domain][setup_integration.entry_id]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    entity_id = "binary_sensor.solar_window_system_test_window_south_shading"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_ON


@pytest.mark.asyncio
async def test_children_factor_reduces_threshold(hass: HomeAssistant, setup_integration):
    """Test that the children_factor correctly reduces the threshold."""
    hass.states.async_set("sun.sun", "above_horizon", {"elevation": 45, "azimuth": 170})
    hass.states.async_set("sensor.dummy_solar_radiation", "450")
    hass.states.async_set("sensor.dummy_indoor_temp_children", "24.0")
    # Set outdoor temp to a value that would trigger shading
    hass.states.async_set("sensor.dummy_outdoor_temp", "24.0")
    hass.config_entries.async_update_entry(
        setup_integration, options={**setup_integration.options, "children_factor": 0.5}
    )
    await hass.async_block_till_done()

    coordinator = hass.data[setup_integration.domain][setup_integration.entry_id]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    entity_id = "binary_sensor.solar_window_system_test_window_children_shading"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_ON


@pytest.mark.asyncio
async def test_temperature_offset_raises_thresholds(hass: HomeAssistant, setup_integration):
    """Test that a temperature offset correctly raises the temperature thresholds."""
    hass.config_entries.async_update_entry(
        setup_integration, options={**setup_integration.options, "temperature_offset": 3.0}
    )
    await hass.async_block_till_done()

    coordinator = hass.data[setup_integration.domain][setup_integration.entry_id]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    entity_id = "binary_sensor.solar_window_system_test_window_south_shading"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_OFF


@pytest.mark.asyncio
async def test_coordinator_defaults_are_correct(hass: HomeAssistant, setup_integration):
    """Test that the internal default values arrive correctly in the coordinator."""
    coordinator = hass.data[setup_integration.domain][setup_integration.entry_id]
    defaults = coordinator.defaults

    assert defaults["physical"]["g_value"] == 0.5
    assert defaults["thresholds"]["direct"] == 200
    assert defaults["temperatures"]["indoor_base"] == 23.0


@pytest.mark.asyncio
async def test_missing_group_falls_back_gracefully(hass: HomeAssistant, setup_integration):
    """Test that the integration does not crash with a missing group."""
    coordinator = hass.data[setup_integration.domain][setup_integration.entry_id]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    entity_id = "binary_sensor.solar_window_system_test_window_bad_group_shading"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_OFF
    assert "No shading required" in state.attributes.get("reason", "")


@pytest.mark.asyncio
async def test_calculation_with_optional_sensor_not_set(hass: HomeAssistant, setup_integration):
    """Test that the calculation remains stable even without optional sensors."""
    hass.states.async_set("sensor.dummy_solar_radiation", "550")
    hass.states.async_set("sun.sun", "above_horizon", {"elevation": 45, "azimuth": 170})
    hass.config_entries.async_update_entry(
        setup_integration, options={**setup_integration.options, "weather_warning_sensor": None}
    )
    await hass.async_block_till_done()

    coordinator = hass.data[setup_integration.domain][setup_integration.entry_id]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    entity_id = "binary_sensor.solar_window_system_test_window_south_shading"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_ON


@pytest.mark.asyncio
async def test_invalid_window_config_is_handled(hass: HomeAssistant, setup_integration):
    """Test that the integration handles a faulty window config gracefully."""
    coordinator = hass.data[setup_integration.domain][setup_integration.entry_id]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert hass.states.get("binary_sensor.solar_window_system_test_window_south_shading") is not None

    faulty_state = hass.states.get("binary_sensor.solar_window_system_test_window_bad_group_shading")
    assert faulty_state is not None
    assert faulty_state.state == STATE_OFF
    # The new behavior is to fall back to default, so no error is expected
    assert "No shading required" in faulty_state.attributes.get("reason", "")


@pytest.mark.asyncio
async def test_unavailable_sensor_is_handled(hass: HomeAssistant, setup_integration):
    """Test that the integration remains stable if a configured sensor is unavailable."""
    hass.states.async_set("sensor.dummy_solar_radiation", "unavailable")
    await hass.async_block_till_done()

    coordinator = hass.data[setup_integration.domain][setup_integration.entry_id]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.solar_window_system_test_window_south_shading")
    assert state is not None
    assert state.state == STATE_OFF