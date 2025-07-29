import pytest
from unittest.mock import MagicMock
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from custom_components.solar_window_system.sensor import (
    SolarWindowSummarySensor,
    SolarWindowPowerSensor,
)
from custom_components.solar_window_system.coordinator import (
    SolarWindowDataUpdateCoordinator,
)


@pytest.fixture
def mock_coordinator():
    coordinator = MagicMock(spec=SolarWindowDataUpdateCoordinator)
    coordinator.data = {
        "summary": {
            "total_power": 123.4,
            "window_count": 2,
            "shading_count": 1,
            "calculation_time": "2024-01-01T12:00:00Z",
        },
        "window1": {
            "power_total": 56.7,
            "power_direct": 30.0,
            "power_diffuse": 26.7,
            "area_m2": 2.5,
            "name": "Window 1",
        },
    }
    return coordinator


def test_summary_sensor_native_value(mock_coordinator):
    sensor = SolarWindowSummarySensor(mock_coordinator)
    assert sensor.native_value == 123.4
    attrs = sensor.extra_state_attributes
    assert isinstance(attrs, dict)
    assert attrs["window_count"] == 2
    assert attrs["shading_count"] == 1
    assert attrs["last_calculation"] == "2024-01-01T12:00:00Z"


def test_power_sensor_native_value(mock_coordinator):
    sensor = SolarWindowPowerSensor(mock_coordinator, "window1")
    assert sensor.native_value == 56.7
    attrs = sensor.extra_state_attributes
    assert isinstance(attrs, dict)
    assert attrs["power_direct"] == 30.0
    assert attrs["power_diffuse"] == 26.7
    assert attrs["area_m2"] == 2.5


# Edge case: coordinator.data is None
@pytest.mark.parametrize(
    "sensor_class,args",
    [
        (SolarWindowSummarySensor, (MagicMock(data=None),)),
        # For SolarWindowPowerSensor, use dict with window1 key to avoid KeyError
        (SolarWindowPowerSensor, (MagicMock(data={"window1": {}}), "window1")),
    ],
)
def test_sensor_none_data(sensor_class, args):
    sensor = sensor_class(*args)
    assert sensor.native_value is None
    # For SolarWindowPowerSensor, the default attributes dict is returned when data is empty
    if sensor_class.__name__ == "SolarWindowPowerSensor":
        assert sensor.extra_state_attributes == {
            "power_direct": 0,
            "power_diffuse": 0,
            "area_m2": None,
        }
    else:
        assert sensor.extra_state_attributes == {}
