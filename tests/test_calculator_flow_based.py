"""
Refactored test suite for the SolarWindowCalculator: geometric shadows, entity caching, flow config, solar power, and integration.
"""

import pytest
from unittest.mock import Mock, patch
from custom_components.solar_window_system.calculator import (
    SolarWindowCalculator,
    WindowCalculationResult,
    SolarCalculationError,
)
from tests.test_data import (
    VALID_WINDOW_DATA,
    VALID_WINDOW_DATA_ALT,
    VALID_PHYSICAL,
    VALID_THRESHOLDS,
    VALID_TEMPERATURES,
)
from homeassistant.config_entries import ConfigEntry


# --- Geometric Shadow Calculation Tests ---
def test_shadow_factor_no_shadow(calculator):
    factor = calculator._calculate_shadow_factor(45, 180, 180, 0, 0)
    assert factor == 1.0


def test_shadow_factor_complete_shadow(calculator):
    factor = calculator._calculate_shadow_factor(10, 180, 180, 2.0, 0.0)
    assert factor == 0.1


def test_shadow_factor_partial_shadow(calculator):
    factor = calculator._calculate_shadow_factor(30, 180, 180, 0.5, 0.2)
    assert 0.1 < factor < 1.0


def test_shadow_factor_low_sun(calculator):
    factor_low = calculator._calculate_shadow_factor(10, 180, 180, 0.5, 0)
    factor_high = calculator._calculate_shadow_factor(60, 180, 180, 0.5, 0)
    assert factor_low < factor_high


def test_shadow_factor_angle_dependency(calculator):
    factor_direct = calculator._calculate_shadow_factor(45, 180, 180, 1.0, 0)
    factor_angled = calculator._calculate_shadow_factor(45, 135, 180, 1.0, 0)
    assert factor_direct <= factor_angled


@pytest.fixture
def calculator(hass):
    mock_entry = Mock(spec=ConfigEntry)
    mock_entry.entry_id = "test_entry"
    return SolarWindowCalculator(hass, mock_entry)


# --- Entity Caching Tests ---
def test_entity_cache_hit(calculator):
    mock_state = Mock()
    mock_state.state = "42.5"
    with patch(
        "homeassistant.core.StateMachine.get", return_value=mock_state
    ) as mock_get:
        result1 = calculator._get_cached_entity_state("sensor.test", 0)
        result2 = calculator._get_cached_entity_state("sensor.test", 0)
        assert result1 == "42.5"
        assert result2 == "42.5"
        assert mock_get.call_count == 1


def test_entity_cache_miss_fallback(calculator):
    with patch("homeassistant.core.StateMachine.get", return_value=None):
        result = calculator._get_cached_entity_state("sensor.missing", "fallback")
        assert result == "fallback"


def test_entity_cache_expiry(calculator):
    calculator._cache_timestamp = 0
    mock_state = Mock()
    mock_state.state = "test_value"
    with patch("homeassistant.core.StateMachine.get", return_value=mock_state):
        result = calculator._get_cached_entity_state("sensor.test", "fallback")
        assert result == "test_value"


# --- Flow Configuration Tests ---
@pytest.fixture
def calculator_with_subentries(hass):
    mock_entry = Mock(spec=ConfigEntry)
    mock_entry.entry_id = "test_entry"
    calculator = SolarWindowCalculator(hass, mock_entry)
    calculator._get_subentries_by_type = Mock()
    calculator._get_subentries_by_type.side_effect = lambda entry_type: {
        "global": {
            "global_config": {
                "physical": {"g_value": 0.7, "frame_width": 0.05},
                "thresholds": {"direct": 400, "diffuse": 200},
                "temperatures": {"indoor_base": 24, "outdoor_base": 25},
            }
        },
        "group": {
            "test_group": {
                "name": "Test Group",
                "physical": {"g_value": 0.8},
                "thresholds": {"direct": 350},
            }
        },
        "window": {
            "test_window": {
                "name": "Test Window",
                "linked_group_id": "test_group",
                "window_width": 1.5,
                "window_height": 2.0,
                "azimuth": 180,
                "shadow_depth": 0.3,
                "physical": {"frame_width": 0.08},
            }
        },
    }[entry_type]
    return calculator


def test_effective_config_inheritance(calculator_with_subentries):
    effective_config, sources = (
        calculator_with_subentries.get_effective_config_from_flows("test_window")
    )
    assert effective_config["physical"]["g_value"] == 0.8
    assert effective_config["physical"]["frame_width"] == 0.08
    assert effective_config["thresholds"]["direct"] == 350
    assert effective_config["thresholds"]["diffuse"] == 200
    assert effective_config["temperatures"]["indoor_base"] == 24
    assert sources["physical"]["g_value"] == "group"
    assert sources["physical"]["frame_width"] == "window"
    assert sources["thresholds"]["direct"] == "group"


def test_effective_config_missing_window(calculator_with_subentries):
    with pytest.raises(ValueError, match="Window configuration not found"):
        calculator_with_subentries.get_effective_config_from_flows("missing_window")


def test_effective_config_missing_group(calculator_with_subentries):
    windows = calculator_with_subentries._get_subentries_by_type("window")
    windows["test_window"]["linked_group_id"] = "missing_group"
    effective_config, sources = (
        calculator_with_subentries.get_effective_config_from_flows("test_window")
    )
    assert effective_config["physical"]["g_value"] == 0.8
    assert sources["physical"]["g_value"] == "group"


# --- Solar Power Calculation Tests ---
@pytest.fixture
def calculator_with_mock_data(hass):
    mock_entry = Mock(spec=ConfigEntry)
    calculator = SolarWindowCalculator(hass, mock_entry)
    calculator.get_effective_config_from_flows = Mock(
        return_value=(
            {
                "physical": {
                    "g_value": 0.7,
                    "frame_width": 0.05,
                    "diffuse_factor": 0.3,
                    "tilt": 0,
                },
                "thresholds": {"direct": 400, "diffuse": 200},
                "temperatures": {"indoor_base": 24, "outdoor_base": 25},
            },
            {},
        )
    )
    calculator._calculate_shadow_factor = Mock(return_value=0.8)
    return calculator


def test_solar_power_calculation_sunny_day(calculator_with_mock_data):
    effective_config = {
        "physical": VALID_PHYSICAL,
        "thresholds": {"direct": VALID_THRESHOLDS["direct"]},
    }
    window_data = VALID_WINDOW_DATA.copy()
    states = {"solar_radiation": 800, "sun_azimuth": 180, "sun_elevation": 45}
    result = calculator_with_mock_data.calculate_window_solar_power_with_shadow(
        effective_config, window_data, states
    )
    assert result.power_total > 0
    assert result.power_direct > 0
    assert result.power_diffuse > 0
    assert result.is_visible is True
    assert result.shadow_factor == 0.8
    assert result.area_m2 == (2.0 - 2 * 0.05) * (1.5 - 2 * 0.05)


def test_solar_power_calculation_no_sun_visibility(calculator_with_mock_data):
    effective_config = {
        "physical": VALID_PHYSICAL,
        "thresholds": {"direct": VALID_THRESHOLDS["direct"]},
    }
    window_data = VALID_WINDOW_DATA_ALT.copy()
    states = {"solar_radiation": 800, "sun_azimuth": 180, "sun_elevation": 45}
    result = calculator_with_mock_data.calculate_window_solar_power_with_shadow(
        effective_config, window_data, states
    )
    assert result.power_direct == 0
    assert result.power_diffuse > 0
    assert result.is_visible is False
    assert result.shadow_factor == 1.0


# --- Integration/Performance Tests ---
@pytest.fixture
def performance_calculator(hass):
    mock_entry = Mock(spec=ConfigEntry)
    mock_entry.data = {"entry_type": "window_configs"}
    calculator = SolarWindowCalculator(hass, mock_entry)
    calculator.global_entry = mock_entry
    windows = {}
    for i in range(50):
        windows[f"window_{i}"] = {
            "name": f"window_{i}",
            "linked_group_id": None,
            "window_width": 1.5,
            "window_height": 1.2,
            "azimuth": (i * 7) % 360,
            "elevation_min": 0,
            "elevation_max": 90,
            "azimuth_min": -45,
            "azimuth_max": 45,
            "shadow_depth": (i % 5) * 0.1,
            "shadow_offset": (i % 3) * 0.1,
            "indoor_temperature_sensor": f"sensor.room_{i}_temp",
        }
    calculator._get_subentries_by_type = Mock()
    calculator._get_subentries_by_type.side_effect = lambda entry_type: {
        "global": {
            "global_config": {
                "physical": {
                    "g_value": 0.7,
                    "frame_width": 0.05,
                    "diffuse_factor": 0.3,
                    "tilt": 0,
                },
                "thresholds": {"direct": 400, "diffuse": 200},
                "temperatures": {"indoor_base": 24, "outdoor_base": 25},
            }
        },
        "group": {},
        "window": windows,
    }[entry_type]
    calculator._get_global_data_merged = Mock(
        return_value={
            "solar_radiation_sensor": "sensor.solar_radiation",
            "outdoor_temperature_sensor": "sensor.outdoor_temp",
            "weather_forecast_temperature_sensor": "sensor.forecast_temp",
            "weather_warning_sensor": "sensor.weather_warning",
        }
    )
    calculator._get_cached_entity_state = Mock(return_value="25")
    calculator.get_safe_attr = Mock(return_value=45)
    calculator.get_scenario_enables_from_entities = Mock(
        return_value={"scenario_b_enabled": False, "scenario_c_enabled": False}
    )
    return calculator


def test_calculation_performance(performance_calculator):
    import time

    start_time = time.time()
    results = performance_calculator.calculate_all_windows_from_flows()
    end_time = time.time()
    calculation_time = end_time - start_time
    assert calculation_time < 1.0
    assert "windows" in results
    assert len(results["windows"]) == 50
    assert "summary" in results


def test_entity_cache_efficiency(performance_calculator):
    performance_calculator.calculate_all_windows_from_flows()
    call_count = performance_calculator._get_cached_entity_state.call_count
    assert call_count < 200
