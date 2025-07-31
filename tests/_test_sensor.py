import pytest
from unittest.mock import MagicMock
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from custom_components.solar_window_system.sensor import (
    SolarWindowSummarySensor,
    SolarWindowPowerSensor,
    async_setup_entry,
)
from custom_components.solar_window_system.coordinator import (
    SolarWindowDataUpdateCoordinator,
)
from custom_components.solar_window_system.const import DOMAIN


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
        "window2": {
            "power_total": 70.0,
            "power_direct": 40.0,
            "power_diffuse": 30.0,
            "area_m2": 3.0,
            "name": "Window 2",
        },
    }
    return coordinator


@pytest.fixture
def mock_hass():
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {} # Initialize hass.data as a dictionary
    return hass


@pytest.mark.asyncio
async def test_async_setup_entry(hass: HomeAssistant, mock_coordinator):
    """Test the sensor setup creates the correct entities."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = mock_coordinator # Correctly set the coordinator
    async_add_entities = MagicMock()

    await async_setup_entry(hass, entry, async_add_entities)

    async_add_entities.assert_called_once()
    entities_added = async_add_entities.call_args[0][0]
    assert len(list(entities_added)) == 3  # 1 summary + 2 window sensors
    
    summary_sensor = next(e for e in entities_added if isinstance(e, SolarWindowSummarySensor))
    window1_sensor = next(e for e in entities_added if isinstance(e, SolarWindowPowerSensor) and e._window_id == "window1")
    window2_sensor = next(e for e in entities_added if isinstance(e, SolarWindowPowerSensor) and e._window_id == "window2")

    assert summary_sensor.unique_id == f"{DOMAIN}_summary_power"
    assert window1_sensor.unique_id == f"{DOMAIN}_window1_power"
    assert window2_sensor.unique_id == f"{DOMAIN}_window2_power"


def test_entity_attributes(mock_coordinator):
    """Test the attributes of the sensor entities."""
    # Summary Sensor
    summary_sensor = SolarWindowSummarySensor(mock_coordinator)
    assert summary_sensor.name == "Summary Power"
    assert summary_sensor.unique_id == f"{DOMAIN}_summary_power"
    assert summary_sensor.device_class == SensorDeviceClass.POWER
    assert summary_sensor.state_class == SensorStateClass.MEASUREMENT
    assert summary_sensor.native_unit_of_measurement == "W"

    # Window Power Sensor
    window_sensor = SolarWindowPowerSensor(mock_coordinator, "window1")
    assert window_sensor.name == "Window 1 Power"
    assert window_sensor.unique_id == f"{DOMAIN}_window1_power"
    assert window_sensor.device_class == SensorDeviceClass.POWER
    assert window_sensor.state_class == SensorStateClass.MEASUREMENT
    assert window_sensor.native_unit_of_measurement == "W"
    assert window_sensor.icon == "mdi:window-maximize"


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


def test_summary_sensor_no_summary_data(mock_coordinator):
    mock_coordinator.data = {}
    sensor = SolarWindowSummarySensor(mock_coordinator)
    assert sensor.native_value is None
    assert sensor.extra_state_attributes == {
        "window_count": None,
        "shading_count": None,
        "last_calculation": None,
    }


def test_power_sensor_no_window_data(mock_coordinator):
    mock_coordinator.data = {"window1": {}}
    sensor = SolarWindowPowerSensor(mock_coordinator, "window1")
    assert sensor.native_value is None
    assert sensor.extra_state_attributes == {
        "power_direct": 0,
        "power_diffuse": 0,
        "area_m2": None,
    }

import pytest
from unittest.mock import MagicMock
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from custom_components.solar_window_system.sensor import (
    SolarWindowSummarySensor,
    SolarWindowPowerSensor,
    async_setup_entry,
)
from custom_components.solar_window_system.coordinator import (
    SolarWindowDataUpdateCoordinator,
)
from custom_components.solar_window_system.const import DOMAIN


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
        "window2": {
            "power_total": 70.0,
            "power_direct": 40.0,
            "power_diffuse": 30.0,
            "area_m2": 3.0,
            "name": "Window 2",
        },
    }
    return coordinator


@pytest.fixture
def mock_hass():
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {} # Initialize hass.data as a dictionary
    return hass


@pytest.mark.asyncio
async def test_async_setup_entry(hass: HomeAssistant, mock_coordinator):
    """Test the sensor setup creates the correct entities."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = mock_coordinator # Correctly set the coordinator
    async_add_entities = MagicMock()

    await async_setup_entry(hass, entry, async_add_entities)

    async_add_entities.assert_called_once()
    entities_added = async_add_entities.call_args[0][0]
    assert len(list(entities_added)) == 3  # 1 summary + 2 window sensors
    
    summary_sensor = next(e for e in entities_added if isinstance(e, SolarWindowSummarySensor))
    window1_sensor = next(e for e in entities_added if isinstance(e, SolarWindowPowerSensor) and e._window_id == "window1")
    window2_sensor = next(e for e in entities_added if isinstance(e, SolarWindowPowerSensor) and e._window_id == "window2")

    assert summary_sensor.unique_id == f"{DOMAIN}_summary_power"
    assert window1_sensor.unique_id == f"{DOMAIN}_window1_power"
    assert window2_sensor.unique_id == f"{DOMAIN}_window2_power"


def test_entity_attributes(mock_coordinator):
    """Test the attributes of the sensor entities."""
    # Summary Sensor
    summary_sensor = SolarWindowSummarySensor(mock_coordinator)
    assert summary_sensor.name == "Summary Power"
    assert summary_sensor.unique_id == f"{DOMAIN}_summary_power"
    assert summary_sensor.device_class == SensorDeviceClass.POWER
    assert summary_sensor.state_class == SensorStateClass.MEASUREMENT
    assert summary_sensor.native_unit_of_measurement == "W"

    # Window Power Sensor
    window_sensor = SolarWindowPowerSensor(mock_coordinator, "window1")
    assert window_sensor.name == "Window 1 Power"
    assert window_sensor.unique_id == f"{DOMAIN}_window1_power"
    assert window_sensor.device_class == SensorDeviceClass.POWER
    assert window_sensor.state_class == SensorStateClass.MEASUREMENT
    assert window_sensor.native_unit_of_measurement == "W"
    assert window_sensor.icon == "mdi:window-maximize"


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


def test_summary_sensor_no_summary_data(mock_coordinator):
    mock_coordinator.data = {}
    sensor = SolarWindowSummarySensor(mock_coordinator)
    assert sensor.native_value is None
    assert sensor.extra_state_attributes == {
        "window_count": None,
        "shading_count": None,
        "last_calculation": None,
    }


def test_power_sensor_no_window_data(mock_coordinator):
    mock_coordinator.data = {"window1": {}}
    sensor = SolarWindowPowerSensor(mock_coordinator, "window1")
    assert sensor.native_value is None
    assert sensor.extra_state_attributes == {
        "power_direct": 0,
        "power_diffuse": 0,
        "area_m2": None,
    }


@pytest.mark.parametrize(
    "missing_key,expected_value,expected_attrs",
    [
        ("total_power", None, {"window_count": 2, "shading_count": 1, "last_calculation": "2024-01-01T12:00:00Z"}),
        ("window_count", 123.4, {"shading_count": 1, "last_calculation": "2024-01-01T12:00:00Z", "window_count": None}),
        ("shading_count", 123.4, {"window_count": 2, "last_calculation": "2024-01-01T12:00:00Z", "shading_count": None}),
        ("calculation_time", 123.4, {"window_count": 2, "shading_count": 1, "last_calculation": None}),
    ],
)
def test_summary_sensor_missing_keys(mock_coordinator, missing_key, expected_value, expected_attrs):
    del mock_coordinator.data["summary"][missing_key]
    sensor = SolarWindowSummarySensor(mock_coordinator)
    assert sensor.native_value == expected_value
    assert sensor.extra_state_attributes == expected_attrs


@pytest.mark.parametrize(
    "missing_key,expected_value,expected_attrs",
    [
        ("power_total", None, {"power_direct": 30.0, "power_diffuse": 26.7, "area_m2": 2.5}),
        ("power_direct", 56.7, {"power_diffuse": 26.7, "area_m2": 2.5, "power_direct": 0}),
        ("power_diffuse", 56.7, {"power_direct": 30.0, "area_m2": 2.5, "power_diffuse": 0}),
        ("area_m2", 56.7, {"power_direct": 30.0, "power_diffuse": 26.7, "area_m2": None}),
        ("name", 56.7, {"power_direct": 30.0, "power_diffuse": 26.7, "area_m2": 2.5}),
    ],
)
def test_power_sensor_missing_keys(mock_coordinator, missing_key, expected_value, expected_attrs):
    del mock_coordinator.data["window1"][missing_key]
    sensor = SolarWindowPowerSensor(mock_coordinator, "window1")
    assert sensor.native_value == expected_value
    assert sensor.extra_state_attributes == expected_attrs


@pytest.mark.parametrize(
    "key,wrong_value,expected_value,expected_attrs",
    [
        ("total_power", "not_a_number", None, {"window_count": 2, "shading_count": 1, "last_calculation": "2024-01-01T12:00:00Z"}),
        ("window_count", "not_a_number", 123.4, {"shading_count": 1, "last_calculation": "2024-01-01T12:00:00Z", "window_count": None}),
        ("shading_count", "not_a_number", 123.4, {"window_count": 2, "last_calculation": "2024-01-01T12:00:00Z", "shading_count": None}),
        ("calculation_time", 123, 123.4, {"window_count": 2, "shading_count": 1, "last_calculation": None}),
    ],
)
def test_summary_sensor_wrong_data_types(mock_coordinator, key, wrong_value, expected_value, expected_attrs):
    mock_coordinator.data["summary"][key] = wrong_value
    sensor = SolarWindowSummarySensor(mock_coordinator)
    assert sensor.native_value == expected_value
    assert sensor.extra_state_attributes == expected_attrs


@pytest.mark.parametrize(
    "key,wrong_value,expected_value,expected_attrs",
    [
        ("power_total", "not_a_number", None, {"power_direct": 30.0, "power_diffuse": 26.7, "area_m2": 2.5}),
        ("power_direct", "not_a_number", 56.7, {"power_diffuse": 26.7, "area_m2": 2.5, "power_direct": 0}),
        ("power_diffuse", "not_a_number", 56.7, {"power_direct": 30.0, "area_m2": 2.5, "power_diffuse": 0}),
        ("area_m2", "not_a_number", 56.7, {"power_direct": 30.0, "power_diffuse": 26.7, "area_m2": None}),
        ("name", 123, 56.7, {"power_direct": 30.0, "power_diffuse": 26.7, "area_m2": 2.5}),
    ],
)
def test_power_sensor_wrong_data_types(mock_coordinator, key, wrong_value, expected_value, expected_attrs):
    mock_coordinator.data["window1"][key] = wrong_value
    sensor = SolarWindowPowerSensor(mock_coordinator, "window1")
    assert sensor.native_value == expected_value
    assert sensor.extra_state_attributes == expected_attrs


@pytest.mark.asyncio
async def test_async_setup_entry_no_data(hass: HomeAssistant, caplog):
    """Test async_setup_entry when coordinator data is None."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    coordinator = MagicMock()
    coordinator.data = None
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator # Correctly set the coordinator
    async_add_entities = MagicMock()

    await async_setup_entry(hass, entry, async_add_entities)

    assert "Coordinator data is None" in caplog.text
    async_add_entities.assert_not_called()
