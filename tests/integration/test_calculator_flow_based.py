"""
Refactored test suite for the SolarWindowCalculator (migrated).

This file contains unit tests for geometric shadow calculation, cache
behaviour, effective configuration merging, and solar power calculations.

Type annotations and docstrings in tests can be noisy; disable ANN001 and
D103 for this test module.
"""

# ruff: noqa: ANN001,D103,S101

from unittest.mock import Mock, patch
import pytest
from homeassistant.config_entries import ConfigEntry

"""Cleaned, minimal tests for SolarWindowCalculator.

This file consolidates the most important and deterministic unit tests used
for refactoring verification. It avoids duplicate fixtures and keeps tests
small so they can be run frequently.
"""

# ruff: noqa: ANN001,D103,S101

from unittest.mock import Mock, patch
import pytest
from homeassistant.config_entries import ConfigEntry

from custom_components.solar_window_system.calculator import SolarWindowCalculator
from tests.test_data import (
    VALID_PHYSICAL,
    VALID_TEMPERATURES,
    VALID_THRESHOLDS,
    VALID_WINDOW_DATA,
)


@pytest.fixture
def calculator(hass, window_entry):
    return SolarWindowCalculator(hass, window_entry)


def test_shadow_factor_no_shadow(calculator) -> None:
    assert calculator._calculate_shadow_factor(45, 180, 180, 0, 0) == 1.0


def test_shadow_factor_complete_shadow(calculator) -> None:
    assert calculator._calculate_shadow_factor(10, 180, 180, 2.0, 0.0) == 0.1


def test_entity_cache_hit(calculator) -> None:
    mock_state = Mock()
    mock_state.state = "42.5"
    with patch(
        "homeassistant.core.StateMachine.get", return_value=mock_state
    ) as mock_get:
        r1 = calculator._get_cached_entity_state("sensor.test", 0)
        r2 = calculator._get_cached_entity_state("sensor.test", 0)
        assert r1 == "42.5"
        assert r2 == "42.5"
        assert mock_get.call_count == 1


def test_recalculation_triggered_on_weather_warning(monkeypatch) -> None:
    mock_entry = Mock(spec=ConfigEntry)
    mock_entry.data = {"entry_type": "window_configs"}
    calc = SolarWindowCalculator(Mock(), mock_entry)

    monkeypatch.setattr(
        calc,
        "_get_subentries_by_type",
        lambda t: {
            "window": {"w1": VALID_WINDOW_DATA.copy()} if t == "window" else {},
            "group": {},
            "global": {"global_config": {}},
        }[t],
    )

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

    monkeypatch.setattr(calc, "_get_cached_entity_state", lambda *a, **kw: "off")
    monkeypatch.setattr(calc, "get_safe_attr", lambda *a, **kw: 0)
    monkeypatch.setattr(
        calc,
        "get_effective_config_from_flows",
        lambda w: (
            {"physical": VALID_PHYSICAL, "thresholds": VALID_THRESHOLDS, "temperatures": VALID_TEMPERATURES},
            {},
        ),
    )
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

    assert call_count["count"] == 2
