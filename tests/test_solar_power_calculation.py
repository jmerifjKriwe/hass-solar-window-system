"""Test solar power calculation logic."""

import math

import pytest
from homeassistant.core import HomeAssistant

from custom_components.solar_window_system.calculator import SolarWindowCalculator


@pytest.fixture
def calculator(hass: HomeAssistant) -> SolarWindowCalculator:
    """Create a calculator instance."""
    return SolarWindowCalculator(hass)


def test_solar_power_calculation_diffuse(calculator: SolarWindowCalculator) -> None:
    """Test the calculation of diffuse solar power."""
    # Test data based on real-world parameters
    window_data = {
        "name": "Test Window",
        "window_width": 1.17,  # 1.17m
        "window_height": 1.25,  # 1.25m
        "frame_width": 0.125,  # 12.5cm frame width
        "g_value": 0.5,  # 50% total energy transmittance
    }

    states = {
        "solar_radiation": 200.0,  # 200 W/m²
        "sun_azimuth": 180.0,
        "sun_elevation": 45.0,
    }

    # Calculate effective glass area (subtracting frame)
    glass_width = window_data["window_width"] - (2 * window_data["frame_width"])
    glass_height = window_data["window_height"] - (2 * window_data["frame_width"])
    glass_area = glass_width * glass_height

    # Set up configuration with diffuse factor
    effective_config = {"diffuse_factor": 0.15}  # 15% diffuse factor

    # Calculate expected diffuse power
    expected_diffuse_power = (
        states["solar_radiation"]
        * effective_config["diffuse_factor"]
        * glass_area
        * window_data["g_value"]
    )

    # Calculate actual values
    result = calculator.calculate_window_solar_power_with_shadow(
        effective_config=effective_config,
        window_data=window_data,
        states=states,
    )

    # Compare expected and actual values
    assert abs(result.power_diffuse - expected_diffuse_power) < 0.1
    assert abs(result.power_diffuse - 13.8) < 0.1  # Should be around 13.8W


def test_solar_power_calculation_direct(calculator: SolarWindowCalculator) -> None:
    """Test the calculation of direct solar power."""
    # Test data
    window_data = {
        "name": "Test Window",
        "window_width": 1.17,
        "window_height": 1.25,
        "frame_width": 0.125,
        "g_value": 0.5,
        "tilt": 90.0,  # Vertical window
        "azimuth": 180.0,  # South facing
    }

    states = {
        "solar_radiation": 200.0,
        "sun_azimuth": 180.0,  # Sun directly south
        "sun_elevation": 45.0,  # 45° elevation
    }

    # Set up configuration with diffuse factor
    effective_config = {"diffuse_factor": 0.15}

    # Calculate actual values
    result = calculator.calculate_window_solar_power_with_shadow(
        effective_config=effective_config,
        window_data=window_data,
        states=states,
    )

    # Calculate effective glass area (subtracting frame)
    glass_width = window_data["window_width"] - (2 * window_data["frame_width"])
    glass_height = window_data["window_height"] - (2 * window_data["frame_width"])
    glass_area = glass_width * glass_height

    # Calculate expected direct power
    sun_elevation_rad = math.radians(states["sun_elevation"])
    sin_sun_el = math.sin(sun_elevation_rad)

    # For vertical window (90°) and sun aligned (180°), cos_incidence = sin(elevation)
    cos_incidence = sin_sun_el

    # Calculate direct power with elevation correction
    expected_direct_power = (
        states["solar_radiation"]
        * (1 - effective_config["diffuse_factor"])  # Account for diffuse portion
        * (
            cos_incidence / sin_sun_el
        )  # Incident angle effect with elevation correction
        * glass_area  # Window area
        * window_data["g_value"]  # Solar heat gain coefficient
    )

    # Compare expected and actual values
    assert abs(result.power_direct - expected_direct_power) < 0.1


def test_solar_power_calculation_shading(calculator: SolarWindowCalculator) -> None:
    """Test the calculation with shadow effects."""
    # Test data with shadow
    window_data = {
        "name": "Test Window",
        "window_width": 1.17,
        "window_height": 1.25,
        "frame_width": 0.125,
        "g_value": 0.5,
        "tilt": 90.0,  # Vertical window
        "azimuth": 180.0,
        "shadow_depth": 0.5,  # 50cm overhang
        "shadow_offset": 0.0,
    }

    states = {
        "solar_radiation": 200.0,
        "sun_azimuth": 180.0,
        "sun_elevation": 45.0,
    }

    # Set up configuration with diffuse factor
    effective_config = {"diffuse_factor": 0.15}

    # Calculate with shadow
    result_with_shadow = calculator.calculate_window_solar_power_with_shadow(
        effective_config=effective_config,
        window_data=window_data,
        states=states,
    )

    # Calculate without shadow for comparison
    window_data_no_shadow = window_data.copy()
    window_data_no_shadow["shadow_depth"] = 0.0
    result_no_shadow = calculator.calculate_window_solar_power_with_shadow(
        effective_config=effective_config,
        window_data=window_data_no_shadow,
        states=states,
    )

    # Shadow should reduce direct radiation but not diffuse
    assert result_with_shadow.power_diffuse == result_no_shadow.power_diffuse
    assert result_with_shadow.power_direct < result_no_shadow.power_direct
    assert result_with_shadow.shadow_factor < 1.0
