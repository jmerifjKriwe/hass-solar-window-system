"""
Unit tests for the CalculationsMixin module.

This test suite provides comprehensive coverage for all implemented calculation methods
in the CalculationsMixin class, including solar power calculations, shadow factors,
and window visibility checks.
"""

import pytest

from custom_components.solar_window_system.modules.calculations import (
    CalculationsMixin,
    SolarCalculationParams,
)
from custom_components.solar_window_system.modules.flow_integration import (
    WindowCalculationResult,
)


class TestCalculationsMixin:
    """Test suite for CalculationsMixin calculation methods."""

    def test_calculate_shadow_factor_no_shadow(self) -> None:
        """Test shadow factor calculation with no shadow geometry."""
        calc = CalculationsMixin()

        # No shadow depth or offset
        result = calc._calculate_shadow_factor(45.0, 180.0, 180.0, 0.0, 0.0)
        assert result == 1.0

    def test_calculate_shadow_factor_full_shadow(self) -> None:
        """Test shadow factor calculation with full shadow."""
        calc = CalculationsMixin()

        # Large shadow depth with direct sun
        result = calc._calculate_shadow_factor(45.0, 180.0, 180.0, 2.0, 0.0)
        assert result == 0.1  # Minimum shadow factor

    def test_calculate_shadow_factor_partial_shadow(self) -> None:
        """Test shadow factor calculation with partial shadow."""
        calc = CalculationsMixin()

        # Moderate shadow with direct sun
        result = calc._calculate_shadow_factor(45.0, 180.0, 180.0, 0.5, 0.0)
        assert 0.1 < result < 1.0

    def test_calculate_shadow_factor_sun_below_horizon(self) -> None:
        """Test shadow factor with sun below horizon."""
        calc = CalculationsMixin()

        result = calc._calculate_shadow_factor(-5.0, 180.0, 180.0, 1.0, 0.0)
        assert result == 1.0  # No shadow when sun is below horizon

    def test_calculate_shadow_factor_azimuth_dependence(self) -> None:
        """Test shadow factor with different azimuth angles."""
        calc = CalculationsMixin()

        # Direct sun (azimuth difference = 0)
        result_direct = calc._calculate_shadow_factor(45.0, 180.0, 180.0, 0.5, 0.0)

        # Angled sun (azimuth difference = 45°)
        result_angled = calc._calculate_shadow_factor(45.0, 225.0, 180.0, 0.5, 0.0)

        # Angled sun should have less shadow effect
        assert result_angled > result_direct

    def test_calculate_shadow_factor_with_offset(self) -> None:
        """Test shadow factor with shadow offset."""
        calc = CalculationsMixin()

        # Shadow depth = 0.5, offset = 0.3, effective shadow = 0.2
        result = calc._calculate_shadow_factor(45.0, 180.0, 180.0, 0.5, 0.3)
        assert result > 0.5  # Less shadow due to offset

    @pytest.mark.parametrize(
        ("sun_elevation", "sun_azimuth", "window_azimuth", "expected"),
        [
            (45.0, 180.0, 180.0, 1.0),  # Direct sun, no shadow
            (45.0, 180.0, 180.0, 0.1),  # Direct sun, full shadow (different depth)
            (0.0, 180.0, 180.0, 1.0),  # Sun at horizon
            (-5.0, 180.0, 180.0, 1.0),  # Sun below horizon
        ],
    )
    def test_calculate_shadow_factor_parametrized(
        self,
        sun_elevation: float,
        sun_azimuth: float,
        window_azimuth: float,
        expected: float,
    ) -> None:
        """Parametrized test for shadow factor calculations."""
        calc = CalculationsMixin()

        if expected == 1.0:
            # No shadow cases
            result = calc._calculate_shadow_factor(
                sun_elevation, sun_azimuth, window_azimuth, 0.0, 0.0
            )
            assert result == expected
        elif expected == 0.1:
            # Full shadow case
            result = calc._calculate_shadow_factor(
                sun_elevation, sun_azimuth, window_azimuth, 2.0, 0.0
            )
            assert result == expected

    def test_calculate_direct_power_direct_sun(self) -> None:
        """Test direct power calculation with direct sun."""
        calc = CalculationsMixin()

        params = {
            "solar_radiation": 1000.0,
            "sun_elevation": 45.0,
            "sun_azimuth": 180.0,
            "diffuse_factor": 0.3,
            "tilt": 90.0,
            "area": 2.0,
            "g_value": 0.8,
        }

        result = calc._calculate_direct_power(params, 180.0)
        assert result > 0

    def test_calculate_direct_power_no_sun(self) -> None:
        """Test direct power calculation with no sun."""
        calc = CalculationsMixin()

        params = {
            "solar_radiation": 1000.0,
            "sun_elevation": -5.0,  # Sun below horizon
            "sun_azimuth": 180.0,
            "diffuse_factor": 0.3,
            "tilt": 90.0,
            "area": 2.0,
            "g_value": 0.8,
        }

        result = calc._calculate_direct_power(params, 180.0)
        assert result == 0.0

    def test_calculate_direct_power_perpendicular_sun(self) -> None:
        """Test direct power with sun perpendicular to window."""
        calc = CalculationsMixin()

        params = {
            "solar_radiation": 1000.0,
            "sun_elevation": 45.0,
            "sun_azimuth": 90.0,  # 90° from window azimuth
            "diffuse_factor": 0.3,
            "tilt": 90.0,
            "area": 2.0,
            "g_value": 0.8,
        }

        result = calc._calculate_direct_power(params, 180.0)
        assert abs(result) < 1e-10  # Should be approximately zero

    def test_calculate_solar_power_direct_wrapper(self) -> None:
        """Test the wrapper method for direct power calculation."""
        calc = CalculationsMixin()

        params = SolarCalculationParams(
            solar_radiation=1000.0,
            sun_elevation=45.0,
            sun_azimuth=180.0,
            window_azimuth=180.0,
            area=2.0,
            g_value=0.8,
            diffuse_factor=0.3,
        )

        result = calc._calculate_solar_power_direct(params)
        assert result > 0

    def test_calculate_solar_power_diffuse(self) -> None:
        """Test diffuse power calculation."""
        calc = CalculationsMixin()

        result = calc._calculate_solar_power_diffuse(
            solar_radiation=1000.0, diffuse_factor=0.3, area=2.0, g_value=0.8
        )

        expected = 1000.0 * 0.3 * 2.0 * 0.8  # 480.0
        assert result == expected

    def test_calculate_total_solar_power(self) -> None:
        """Test total solar power calculation."""
        calc = CalculationsMixin()

        result = calc._calculate_total_solar_power(
            solar_radiation=1000.0, diffuse_factor=0.3, area=2.0, g_value=0.8
        )

        # Should be direct + diffuse
        assert result > 0

    def test_calculate_power_per_square_meter(self) -> None:
        """Test power per square meter calculation."""
        calc = CalculationsMixin()

        # Normal case
        result = calc._calculate_power_per_square_meter(total_power=1000.0, area=2.0)
        assert result == 500.0

        # Edge case: zero area
        result = calc._calculate_power_per_square_meter(total_power=1000.0, area=0.0)
        assert result == 0.0

    def test_check_window_visibility_visible(self) -> None:
        """Test window visibility check when sun is visible."""
        calc = CalculationsMixin()

        window_data = {
            "azimuth": 180.0,
            "elevation_min": 0.0,
            "elevation_max": 90.0,
            "azimuth_min": -45.0,
            "azimuth_max": 45.0,
        }

        is_visible, window_azimuth = calc._check_window_visibility(
            sun_elevation=45.0, sun_azimuth=180.0, window_data=window_data
        )

        assert is_visible is True
        assert window_azimuth == 180.0

    def test_check_window_visibility_not_visible_elevation(self) -> None:
        """Test window visibility when sun elevation is outside range."""
        calc = CalculationsMixin()

        window_data = {
            "azimuth": 180.0,
            "elevation_min": 30.0,
            "elevation_max": 60.0,
            "azimuth_min": -45.0,
            "azimuth_max": 45.0,
        }

        is_visible, window_azimuth = calc._check_window_visibility(
            sun_elevation=15.0,  # Below minimum elevation
            sun_azimuth=180.0,
            window_data=window_data,
        )

        assert is_visible is False
        assert window_azimuth == 180.0

    def test_check_window_visibility_not_visible_azimuth(self) -> None:
        """Test window visibility when sun azimuth is outside range."""
        calc = CalculationsMixin()

        window_data = {
            "azimuth": 180.0,
            "elevation_min": 0.0,
            "elevation_max": 90.0,
            "azimuth_min": -30.0,
            "azimuth_max": 30.0,
        }

        is_visible, window_azimuth = calc._check_window_visibility(
            sun_elevation=45.0,
            sun_azimuth=220.0,  # Outside azimuth range
            window_data=window_data,
        )

        assert is_visible is False
        assert window_azimuth == 180.0

    def test_check_window_visibility_with_effective_config(self) -> None:
        """Test window visibility with effective config override."""
        calc = CalculationsMixin()

        window_data = {"azimuth": 180.0}
        effective_config = {
            "azimuth": 200.0,
            "elevation_min": 20.0,
            "elevation_max": 70.0,
            "azimuth_min": -20.0,
            "azimuth_max": 20.0,
        }

        is_visible, window_azimuth = calc._check_window_visibility(
            sun_elevation=45.0,
            sun_azimuth=200.0,
            window_data=window_data,
            effective_config=effective_config,
        )

        assert is_visible is True
        assert window_azimuth == 200.0

    def test_check_window_visibility_default_values(self) -> None:
        """Test window visibility with default configuration values."""
        calc = CalculationsMixin()

        window_data = {}  # Empty config, should use defaults

        is_visible, window_azimuth = calc._check_window_visibility(
            sun_elevation=45.0, sun_azimuth=180.0, window_data=window_data
        )

        assert is_visible is True
        assert window_azimuth == 180.0  # Default azimuth

    def test_placeholder_methods_raise_not_implemented(self) -> None:
        """Test that placeholder methods are now implemented and work correctly."""
        calc = CalculationsMixin()

        # Test main calculation method - now implemented
        result = calc.calculate_window_solar_power_with_shadow(
            {"shadow_depth": 1.0, "shadow_offset": 0.0},
            {"id": "test_window", "area": 2.0, "azimuth": 180.0},
            {},
        )

        # Verify the result structure
        assert isinstance(result, WindowCalculationResult)
        assert result.power_total >= 0
        assert result.shadow_factor >= 0
        assert isinstance(result.shade_required, bool)

        # Test parameter extraction method - now implemented
        result = calc._extract_calculation_parameters(
            {"solar_elevation": 45.0, "solar_azimuth": 180.0},
            {"window_azimuth": 180.0, "window_area": 2.0},
            {"shadow_factor": 0.8},
        )
        assert isinstance(result, tuple)
        assert len(result) == 9  # Should return 9 parameters

    @pytest.mark.parametrize(
        ("total_power", "area", "expected"),
        [
            (1000.0, 2.0, 500.0),
            (500.0, 1.0, 500.0),
            (0.0, 2.0, 0.0),
            (1000.0, 0.0, 0.0),
            (1000.0, -1.0, 0.0),
        ],
    )
    def test_calculate_power_per_square_meter_parametrized(
        self, total_power: float, area: float, expected: float
    ) -> None:
        """Parametrized test for power per square meter calculation."""
        calc = CalculationsMixin()
        result = calc._calculate_power_per_square_meter(total_power, area)
        assert result == expected
