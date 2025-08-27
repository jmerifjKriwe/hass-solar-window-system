"""
Integration tests for SolarWindowCalculator.

This module contains integration-style tests; it purposefully keeps a few
deterministic, fast tests that exercise calculation logic and flow
inheritance. To reduce noisy linter findings in tests we allow a small
set of test-only rules here.
"""

# ruff: noqa: ANN001, D103, E501, SLF001, S101, ARG005

from unittest.mock import Mock, patch

import pytest

from custom_components.solar_window_system.calculator import SolarWindowCalculator
from homeassistant.config_entries import ConfigEntry
from tests.test_data import (
    VALID_PHYSICAL,
    VALID_TEMPERATURES,
    VALID_THRESHOLDS,
    VALID_WINDOW_DATA,
)

# Test constants to avoid magic numbers in assertions
EXPECTED_NO_SHADOW = 1.0
EXPECTED_COMPLETE_SHADOW = 0.1
EXPECTED_TRIGGER_COUNT = 2


@pytest.fixture
def calculator(hass, window_entry):
    """Provide a SolarWindowCalculator using the canonical `window_entry` fixture."""
    return SolarWindowCalculator(hass, window_entry)


def test_shadow_factor_no_shadow(calculator):
    assert calculator._calculate_shadow_factor(45, 180, 180, 0, 0) == EXPECTED_NO_SHADOW


def test_shadow_factor_complete_shadow(calculator):
    assert calculator._calculate_shadow_factor(10, 180, 180, 2.0, 0.0) == EXPECTED_COMPLETE_SHADOW


def test_entity_cache_hit(calculator):
    mock_state = Mock()
    mock_state.state = "42.5"
    with patch("homeassistant.core.StateMachine.get", return_value=mock_state) as mock_get:
        r1 = calculator._get_cached_entity_state("sensor.test", 0)
        r2 = calculator._get_cached_entity_state("sensor.test", 0)
        assert r1 == "42.5"
        assert r2 == "42.5"
        assert mock_get.call_count == 1


def test_scenario_b_c_inheritance(monkeypatch, hass):
    """Test scenario B/C enable inheritance and override logic (window > group > global)."""
    mock_entry = Mock(spec=ConfigEntry)
    mock_entry.data = {"entry_type": "window_configs"}
    calc = SolarWindowCalculator(hass, mock_entry)

    windows = {
        "w_global": {"name": "GlobalWin", "parent_group_id": "g1"},
        "w_group": {"name": "GroupWin", "parent_group_id": "g2"},
        "w_window": {
            "name": "WindowWin",
            "parent_group_id": "g3",
            "scenario_b_enable": "enable",
            "scenario_c_enable": "disable",
        },
    }
    groups = {
        "g1": {"name": "Group1"},
        "g2": {"name": "Group2", "scenario_b_enable": "disable", "scenario_c_enable": "enable"},
        "g3": {"name": "Group3", "scenario_b_enable": "disable", "scenario_c_enable": "enable"},
    }

    def _subentries_scenario(t):
        return windows if t == "window" else (groups if t == "group" else {})

    monkeypatch.setattr(calc, "_get_subentries_by_type", _subentries_scenario)

    global_states = {"scenario_b_enabled": True, "scenario_c_enabled": True}

    b, c = calc._get_scenario_enables_from_flows("w_global", global_states)
    assert b is True
    assert c is True

    b, c = calc._get_scenario_enables_from_flows("w_group", global_states)
    assert b is False
    assert c is True

    b, c = calc._get_scenario_enables_from_flows("w_window", global_states)
    assert b is True
    assert c is False


def test_recalculation_triggered_on_weather_warning(monkeypatch):
    """Ensure calculator recalculates when weather warning state changes."""
    mock_entry = Mock(spec=ConfigEntry)
    mock_entry.data = {"entry_type": "window_configs"}
    calc = SolarWindowCalculator(Mock(), mock_entry)

    def _subentries_recalc(t):
        return {
            "window": {"w1": VALID_WINDOW_DATA.copy()} if t == "window" else {},
            "group": {},
            "global": {"global_config": {}},
        }[t]

    monkeypatch.setattr(calc, "_get_subentries_by_type", _subentries_recalc)

    monkeypatch.setattr(
        calc,
        "_get_global_data_merged",
        lambda: {
            "solar_radiation_sensor": "sensor.solar_radiation",
            "outdoor_temperature_sensor": "sensor.outdoor_temp",
            "weather_forecast_temperature_sensor": "sensor.forecast_temp",
            "weather_warning_sensor": "sensor.weather_warning",
        },
    )

    monkeypatch.setattr(calc, "_get_cached_entity_state", lambda *a, **kw: 0)
    monkeypatch.setattr(calc, "get_safe_attr", lambda *a, **kw: 0)
    def _get_effective_config_from_flows(_w):
        return ({
            "physical": VALID_PHYSICAL,
            "thresholds": VALID_THRESHOLDS,
            "temperatures": VALID_TEMPERATURES,
        }, {})

    monkeypatch.setattr(calc, "get_effective_config_from_flows", _get_effective_config_from_flows)
    monkeypatch.setattr(calc, "apply_global_factors", lambda c, g, e: c)
    monkeypatch.setattr(calc, "_should_shade_window_from_flows", lambda req: (True, "Should shade"))
    monkeypatch.setattr(calc, "_get_scenario_enables_from_flows", lambda w, e: (False, False))

    call_count = {"count": 0}
    orig_calc = calc.calculate_all_windows_from_flows

    def counting_calc():
        call_count["count"] += 1
        return orig_calc()

    monkeypatch.setattr(calc, "calculate_all_windows_from_flows", counting_calc)

    monkeypatch.setattr(calc, "_get_cached_entity_state", lambda *a, **kw: "off")
    calc.calculate_all_windows_from_flows()
    monkeypatch.setattr(calc, "_get_cached_entity_state", lambda *a, **kw: "on")
    calc.calculate_all_windows_from_flows()

    assert call_count["count"] == EXPECTED_TRIGGER_COUNT

