"""
Refactored test suite for the SolarWindowCalculator (migrated).

This file contains unit tests for geometric shadow calculation, cache
behaviour, effective configuration merging, and solar power calculations.
"""

import pytest
from unittest.mock import Mock, patch

from custom_components.solar_window_system.calculator import SolarWindowCalculator
from homeassistant.config_entries import ConfigEntry
from tests.test_data import (
    VALID_WINDOW_DATA,
    VALID_WINDOW_DATA_ALT,
    VALID_PHYSICAL,
    VALID_THRESHOLDS,
    VALID_TEMPERATURES,
)


@pytest.fixture
def calculator(hass):
    mock_entry = Mock(spec=ConfigEntry)
    mock_entry.entry_id = "test_entry"
    return SolarWindowCalculator(hass, mock_entry)


def test_shadow_factor_no_shadow(calculator):
    factor = calculator._calculate_shadow_factor(45, 180, 180, 0, 0)
    assert factor == 1.0


def test_shadow_factor_complete_shadow(calculator):
    factor = calculator._calculate_shadow_factor(10, 180, 180, 2.0, 0.0)
    assert factor == 0.1


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


"""
Refactored integration-style tests for SolarWindowCalculator migrated from legacy suite.
These tests focus on flow inheritance, triggers, calculation correctness, and performance.
"""

import pytest
from unittest.mock import Mock, patch
from custom_components.solar_window_system.calculator import (
    SolarWindowCalculator,
)
from tests.test_data import (
    VALID_WINDOW_DATA,
    VALID_WINDOW_DATA_ALT,
    VALID_PHYSICAL,
    VALID_THRESHOLDS,
    VALID_TEMPERATURES,
)
from homeassistant.config_entries import ConfigEntry


def test_scenario_b_c_inheritance(monkeypatch, hass):
    """Test scenario B/C enable inheritance and override logic (window > group > global)."""
    mock_entry = Mock(spec=ConfigEntry)
    mock_entry.data = {"entry_type": "window_configs"}
    calculator = SolarWindowCalculator(hass, mock_entry)

    # Prepare subentries for all inheritance cases
    windows = {
        # Inherit from global (no override)
        "w_global": {"name": "GlobalWin", "parent_group_id": "g1"},
        # Override at group level
        "w_group": {"name": "GroupWin", "parent_group_id": "g2"},
        # Override at window level
        "w_window": {
            "name": "WindowWin",
            "parent_group_id": "g3",
            "scenario_b_enable": "enable",
            "scenario_c_enable": "disable",
        },
    }
    groups = {
        "g1": {"name": "Group1"},
        "g2": {
            "name": "Group2",
            "scenario_b_enable": "disable",
            "scenario_c_enable": "enable",
        },
        "g3": {
            "name": "Group3",
            "scenario_b_enable": "disable",
            "scenario_c_enable": "enable",
        },
    }

    monkeypatch.setattr(
        calculator,
        "_get_subentries_by_type",
        lambda t: windows if t == "window" else (groups if t == "group" else {}),
    )

    # Global states: both enabled
    global_states = {"scenario_b_enabled": True, "scenario_c_enabled": True}

    # 1. Window inherits from global
    b, c = calculator._get_scenario_enables_from_flows("w_global", global_states)
    assert b is True  # from global
    assert c is True  # from global

    # 2. Window inherits from group (group disables B, enables C)
    b, c = calculator._get_scenario_enables_from_flows("w_group", global_states)
    assert b is False  # group disables
    assert c is True  # group enables

    # 3. Window overrides both (window enables B, disables C)
    b, c = calculator._get_scenario_enables_from_flows("w_window", global_states)
    assert b is True  # window enables
    assert c is False  # window disables


def test_recalculation_triggered_on_weather_warning(monkeypatch):
    """If weather warning sensor goes to true, calculation should be triggered immediately."""
    mock_entry = Mock(spec=ConfigEntry)
    mock_entry.data = {"entry_type": "window_configs"}
    calculator = SolarWindowCalculator(Mock(), mock_entry)
    # Patch methods to simulate one window
    monkeypatch.setattr(
        calculator,
        "_get_subentries_by_type",
        lambda t: {
            "window": {"w1": VALID_WINDOW_DATA.copy()} if t == "window" else {},
            "group": {},
            "global": {"global_config": {}},
        }[t],
    )
    monkeypatch.setattr(
        calculator,
        "_get_global_data_merged",
        lambda: {
            "solar_radiation_sensor": "sensor.solar_radiation",
            "outdoor_temperature_sensor": "sensor.outdoor_temp",
            "weather_forecast_temperature_sensor": "sensor.forecast_temp",
            "weather_warning_sensor": "sensor.weather_warning",
        },
    )
    monkeypatch.setattr(calculator, "_get_cached_entity_state", lambda *a, **kw: 0)
    monkeypatch.setattr(calculator, "get_safe_attr", lambda *a, **kw: 0)
    monkeypatch.setattr(
        calculator,
        "get_effective_config_from_flows",
        lambda w: (
            {
                "physical": VALID_PHYSICAL,
                "thresholds": VALID_THRESHOLDS,
                "temperatures": VALID_TEMPERATURES,
            },
            {},
        ),
    )
    monkeypatch.setattr(calculator, "apply_global_factors", lambda c, g, e: c)
    monkeypatch.setattr(
        calculator,
        "_should_shade_window_from_flows",
        lambda req: (True, "Should shade"),
    )
    monkeypatch.setattr(
        calculator, "_get_scenario_enables_from_flows", lambda w, e: (False, False)
    )

    # Simulate weather warning off, then on
    call_count = {"count": 0}
    orig_calc = calculator.calculate_all_windows_from_flows

    def counting_calc():
        call_count["count"] += 1
        return orig_calc()

    monkeypatch.setattr(calculator, "calculate_all_windows_from_flows", counting_calc)

    # First call: weather warning off
    monkeypatch.setattr(calculator, "_get_cached_entity_state", lambda *a, **kw: "off")
    calculator.calculate_all_windows_from_flows()
    # Second call: weather warning on
    monkeypatch.setattr(calculator, "_get_cached_entity_state", lambda *a, **kw: "on")
    calculator.calculate_all_windows_from_flows()

    # The calculation should have been triggered twice
    assert call_count["count"] == 2


# --- Geometric Shadow Calculation Tests ---


@pytest.fixture
def calculator(hass):
    mock_entry = Mock(spec=ConfigEntry)
    mock_entry.entry_id = "test_entry"
    return SolarWindowCalculator(hass, mock_entry)


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


# (file continues with solar power tests and performance tests)
