"""Test the calculator logic of the solar_window_system component."""
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.const import STATE_ON, STATE_OFF

from custom_components.solar_window_system.calculator import SolarWindowCalculator
from .conftest import setup_integration
from .mocks import MOCK_CONFIG


def test_calculator_creation(hass: HomeAssistant):
    """Test the creation of a calculator object."""
    calculator = SolarWindowCalculator(hass, {}, MOCK_CONFIG["groups"], MOCK_CONFIG["windows"])

    assert calculator is not None
    assert len(calculator.windows) == 5


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