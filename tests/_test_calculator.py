"""Test the calculator logic of the solar_window_system component."""
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_ON, STATE_OFF

from .conftest import setup_integration


@pytest.mark.asyncio
async def test_calculator_creation(hass: HomeAssistant, setup_integration):
    """Test the creation of a calculator object."""
    coordinator = hass.data[setup_integration.domain][setup_integration.entry_id]
    calculator = coordinator.calculator

    assert calculator is not None
    assert len(calculator.windows) == 1


@pytest.mark.parametrize(
    ("solar_radiation", "expected_state", "expected_power", "expected_reason_part"),
    [
        ("800", STATE_ON, 1206.8, "Strong sun"),
        ("50", STATE_OFF, 75.4, "No shading required"),
    ],
)
async def test_shading_calculation(
    hass: HomeAssistant,
    setup_integration,
    solar_radiation: str,
    expected_state: str,
    expected_power: float,
    expected_reason_part: str,
):
    """Test the shading logic and validate the calculation results."""
    hass.states.async_set("sun.sun", "above_horizon", {"azimuth": 170, "elevation": 45})
    hass.states.async_set("sensor.dummy_solar_radiation", solar_radiation)
    await hass.async_block_till_done()

    # Manually trigger a refresh of the coordinator
    coordinator = hass.data[setup_integration.domain][setup_integration.entry_id]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    entity_id = "binary_sensor.solar_window_system_test_window_south_shading"
    state = hass.states.get(entity_id)

    assert state is not None, f"Shading sensor '{entity_id}' was not created."
    assert state.state == expected_state, f"Expected state '{expected_state}', but got '{state.state}'."

    calculated_power = state.attributes.get("power_total_w")
    assert calculated_power == pytest.approx(expected_power, rel=0.01)

    reason = state.attributes.get("reason")
    assert isinstance(reason, str)
    assert expected_reason_part in reason

    # Test the power sensor
    power_entity_id = "sensor.solar_window_system_test_window_south_power"
    power_state = hass.states.get(power_entity_id)
    assert power_state is not None, f"Power sensor '{power_entity_id}' was not created."
    assert power_state.state == str(calculated_power)


@pytest.mark.parametrize(
    ("elevation", "expected_state"),
    [
        (5, STATE_OFF),
        (15, STATE_ON),
    ],
)
async def test_sun_elevation(
    hass: HomeAssistant,
    setup_integration,
    elevation: int,
    expected_state: str,
):
    """Test the sun elevation logic."""
    hass.states.async_set("sun.sun", "above_horizon", {"azimuth": 170, "elevation": elevation})
    hass.states.async_set("sensor.dummy_solar_radiation", "800")
    await hass.async_block_till_done()

    # Manually trigger a refresh of the coordinator
    coordinator = hass.data[setup_integration.domain][setup_integration.entry_id]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    entity_id = "binary_sensor.solar_window_system_test_window_south_shading"
    state = hass.states.get(entity_id)

    assert state is not None, f"Shading sensor '{entity_id}' was not created."
    assert state.state == expected_state, f"Expected state '{expected_state}', but got '{state.state}'."


@pytest.mark.parametrize(
    ("azimuth", "expected_state"),
    [
        (80, STATE_OFF),
        (170, STATE_ON),
    ],
)
async def test_sun_azimuth(
    hass: HomeAssistant,
    setup_integration,
    azimuth: int,
    expected_state: str,
):
    """Test the sun azimuth logic."""
    hass.states.async_set("sun.sun", "above_horizon", {"azimuth": azimuth, "elevation": 45})
    hass.states.async_set("sensor.dummy_solar_radiation", "800")
    await hass.async_block_till_done()

    # Manually trigger a refresh of the coordinator
    coordinator = hass.data[setup_integration.domain][setup_integration.entry_id]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    entity_id = "binary_sensor.solar_window_system_test_window_south_shading"
    state = hass.states.get(entity_id)

    assert state is not None, f"Shading sensor '{entity_id}' was not created."
    assert state.state == expected_state, f"Expected state '{expected_state}', but got '{state.state}'."


@pytest.mark.parametrize(
    ("weather_state", "expected_state"),
    [
        ("on", STATE_ON),
        ("off", STATE_OFF),
    ],
)
async def test_weather_warning(
    hass: HomeAssistant,
    setup_integration,
    weather_state: str,
    expected_state: str,
):
    """Test the weather warning logic."""
    hass.states.async_set("sun.sun", "above_horizon", {"azimuth": 170, "elevation": 45})
    hass.states.async_set("sensor.dummy_solar_radiation", "800")
    hass.states.async_set("binary_sensor.dummy_weather_warning", weather_state)
    await hass.async_block_till_done()

    # Manually trigger a refresh of the coordinator
    coordinator = hass.data[setup_integration.domain][setup_integration.entry_id]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    entity_id = "binary_sensor.solar_window_system_test_window_south_shading"
    state = hass.states.get(entity_id)

    assert state is not None, f"Shading sensor '{entity_id}' was not created."
    assert state.state == expected_state, f"Expected state '{expected_state}', but got '{state.state}'."
