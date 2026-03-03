"""Tests for the Solar Window System constants."""

import pytest

from custom_components.solar_window_system.const import (
    DOMAIN,
    DEFAULT_FORECAST_HIGH,
    DEFAULT_INSIDE_TEMP,
    DEFAULT_OUTSIDE_TEMP,
    DEFAULT_SOLAR_ENERGY,
    ENERGY_TYPE_COMBINED,
    ENERGY_TYPE_DIFFUSE,
    ENERGY_TYPE_DIRECT,
)


def test_domain_is_defined():
    """Test that the domain is correctly defined."""
    assert DOMAIN == "solar_window_system"


def test_defaults_are_positive():
    """Test that default threshold values are positive."""
    assert DEFAULT_OUTSIDE_TEMP > 0
    assert DEFAULT_INSIDE_TEMP > 0
    assert DEFAULT_SOLAR_ENERGY > 0
    assert DEFAULT_FORECAST_HIGH > 0


def test_energy_types():
    """Test that energy types are correctly defined."""
    assert ENERGY_TYPE_DIRECT == "direct"
    assert ENERGY_TYPE_DIFFUSE == "diffuse"
    assert ENERGY_TYPE_COMBINED == "combined"
