"""Test that custom configuration values are correctly used in calculations."""

from __future__ import annotations

from enum import Enum, auto
from typing import Any

import pytest
import math
from custom_components.solar_window_system.modules.calculations import (
    WindowCalculationResult,
    CalculationsMixin,
)

from tests.test_data import (
    VALID_PHYSICAL,
    VALID_THRESHOLDS,
    VALID_TEMPERATURES,
    VALID_SOLAR_DATA,
)


class ShadingState(Enum):
    """Enum for shading states."""

    SHADING_REQUIRED = auto()
    NO_SHADING = auto()


class TestEffectiveConfigValues:
    """Test suite for verifying that custom configuration values are used correctly."""

    def setup_method(self) -> None:
        """Set up test cases."""
        self.calc = CalculationsMixin()
        self.window_data = {
            "area": 2.0,
            "azimuth": 180.0,
            "window_width": 2.0,
            "window_height": 1.0,
        }
        self.states = {
            "sun_elevation": VALID_SOLAR_DATA["elevation"],
            "sun_azimuth": VALID_SOLAR_DATA["azimuth"],
            "solar_radiation": VALID_SOLAR_DATA["radiation"],
        }

    @pytest.mark.parametrize(
        ("config_value", "expected_power"),
        [
            # Expected values computed from the calculator formula used in
            # `calculate_window_solar_power_with_shadow` (includes angle and
            # diffuse components):
            # The implementation computes total power per window using the
            # formula: solar radiation times g_value times (cosine of
            # elevation + diffuse factor) times area
            ({"physical": {"g_value": 0.5}}, 685.6854249492381),
            ({"physical": {"g_value": 0.7}}, 959.9595949289333),
            ({"physical": {"g_value": 0.3}}, 411.41125496954286),
        ],
    )
    def test_g_value_affects_power(
        self, config_value: dict[str, Any], expected_power: float
    ) -> None:
        """Test that g_value from effective config affects calculated power."""
        result = self.calc.calculate_window_solar_power_with_shadow(
            config_value, self.window_data, self.states
        )
        assert isinstance(result, WindowCalculationResult)
        assert pytest.approx(result.power_total, 0.1) == expected_power

    @pytest.mark.parametrize(
        ("config_value", "expected_factor"),
        [
            # Test with default diffuse_factor (0.15)
            ({"physical": {"diffuse_factor": 0.15}}, 0.15),
            # Test with custom diffuse_factor from VALID_PHYSICAL (0.3)
            ({"physical": {"diffuse_factor": 0.3}}, 0.3),
            # Test with very low diffuse_factor
            ({"physical": {"diffuse_factor": 0.05}}, 0.05),
        ],
    )
    def test_diffuse_factor_affects_radiation_split(
        self, config_value: dict[str, Any], expected_factor: float
    ) -> None:
        """Test diffuse_factor config effect on radiation split."""
        result = self.calc.calculate_window_solar_power_with_shadow(
            config_value, self.window_data, self.states
        )
        assert isinstance(result, WindowCalculationResult)

        # Calculate expected diffuse power. The calculation in the code
        # applies the window's g_value (default 0.5 when not provided), so
        # include it here to have a fixed expected number.
        area = self.window_data["area"]
        radiation = self.states["solar_radiation"]
        g_value = 0.5
        expected_diffuse = radiation * expected_factor * g_value * area

        assert pytest.approx(result.power_diffuse, 0.1) == expected_diffuse

    @pytest.mark.parametrize(
        ("config_value", "total_power", "expected_shade"),
        [
            # Test with default threshold (200 W)
            ({"thresholds": {"direct": 200}}, 800.0, ShadingState.SHADING_REQUIRED),
            # Test with custom threshold from VALID_THRESHOLDS (400 W)
            ({"thresholds": {"direct": 400}}, 300.0, ShadingState.NO_SHADING),
            # Test with custom threshold from VALID_THRESHOLDS (400 W)
            ({"thresholds": {"direct": 400}}, 500.0, ShadingState.SHADING_REQUIRED),
        ],
    )
    def test_threshold_affects_shading(
        self,
        config_value: dict[str, Any],
        total_power: float,
        expected_shade: ShadingState,
    ) -> None:
        """Test that threshold from effective config affects shading decision."""
        # Modify window area to achieve desired total power. The calculator
        # computes total power as:
        #   The implementation computes total as: solar radiation times
        #   g_value times (cosine of elevation + diffuse factor) times area
        # Use that formula (with default g_value=0.5 and diffuse_factor=0.15).
        cos_el = math.cos(math.radians(self.states["sun_elevation"]))
        g_value = 0.5
        diffuse_factor = 0.15
        denom = self.states["solar_radiation"] * g_value * (cos_el + diffuse_factor)
        desired_area = total_power / denom
        # The CalculationsMixin implementation prefers an explicit 'area'
        # value; remove it so the mixin computes area from window dimensions
        # (window_width * window_height). Set these so the effective area
        # matches the desired area for the test case.
        self.window_data.pop("area", None)
        # The calculation subtracts frame width from both dimensions when
        # computing glass area. Compute window_width so that the resulting
        # glass area matches the desired_area. Use the default frame width
        # as used in the implementation (0.125 m).
        frame_width = 0.125
        self.window_data["window_height"] = 1.0
        glass_height = max(0.0, self.window_data["window_height"] - 2 * frame_width)
        # Avoid division by zero in edge cases; if glass_height is zero, fall
        # back to setting width equal to desired_area (will yield zero area).
        if glass_height <= 0:
            window_width = desired_area
        else:
            glass_width = desired_area / glass_height
            window_width = glass_width + 2 * frame_width
        self.window_data["window_width"] = window_width

        result = self.calc.calculate_window_solar_power_with_shadow(
            config_value, self.window_data, self.states
        )
        assert isinstance(result, WindowCalculationResult)
        is_shading_required = expected_shade == ShadingState.SHADING_REQUIRED
        assert result.shade_required == is_shading_required

    def test_full_custom_config(self) -> None:
        """Test that all custom values from VALID_* constants work together."""
        effective_config = {
            "physical": VALID_PHYSICAL,
            "thresholds": VALID_THRESHOLDS,
            "temperatures": VALID_TEMPERATURES,
        }

        result = self.calc.calculate_window_solar_power_with_shadow(
            effective_config, self.window_data, self.states
        )
        assert isinstance(result, WindowCalculationResult)

        # Verify g_value affect (0.7 instead of default 0.5).
        # Use the same calculation as the implementation (angle + diffuse).
        cos_el = math.cos(math.radians(self.states["sun_elevation"]))
        g_value = VALID_PHYSICAL["g_value"]
        diffuse_factor = VALID_PHYSICAL["diffuse_factor"]
        expected_power = (
            self.states["solar_radiation"]
            * g_value
            * (cos_el + diffuse_factor)
            * self.window_data["area"]
        )
        assert pytest.approx(result.power_total, 0.1) == expected_power

        # Verify diffuse_factor effect (0.3 instead of default 0.15)
        expected_diffuse = (
            self.states["solar_radiation"]
            * self.window_data["area"]
            * g_value
            * diffuse_factor
        )
        assert pytest.approx(result.power_diffuse, 0.1) == expected_diffuse

        # Verify threshold effect (400 instead of default 200)
        threshold = VALID_THRESHOLDS["direct"]
        is_shading_required = result.power_total > threshold
        assert result.shade_required == is_shading_required
