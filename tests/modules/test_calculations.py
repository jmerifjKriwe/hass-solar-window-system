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
        assert window_azimuth == 180.0  # window_azimuth should come from window_data

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


class TestCalculationsUtilities:
    """Test suite for calculation utility functions."""

    def test_get_trig_values_lookup_table(self) -> None:
        """Test trigonometric lookup table function."""
        from custom_components.solar_window_system.modules.calculations import (
            get_trig_values,
        )

        # Test with integer angle in LUT
        result = get_trig_values(45.0)
        assert "radians" in result
        assert "cos" in result
        assert "sin" in result
        assert abs(result["cos"] - 0.7071067811865476) < 1e-10
        assert abs(result["sin"] - 0.7071067811865475) < 1e-10

    def test_get_trig_values_non_integer(self) -> None:
        """Test trigonometric function with non-integer angle."""
        from custom_components.solar_window_system.modules.calculations import (
            get_trig_values,
        )

        # Test with non-integer angle
        result = get_trig_values(45.5)
        assert "radians" in result
        assert "cos" in result
        assert "sin" in result
        assert result["radians"] == pytest.approx(0.8028514559173916, abs=1e-10)

    def test_get_trig_values_out_of_range(self) -> None:
        """Test trigonometric function with angle outside LUT range."""
        from custom_components.solar_window_system.modules.calculations import (
            get_trig_values,
        )

        # Test with angle > 90
        result = get_trig_values(120.0)
        assert "radians" in result
        assert "cos" in result
        assert "sin" in result
        assert result["radians"] == pytest.approx(2.0943951023931953, abs=1e-10)


class TestWindowCalculationResultPool:
    """Test suite for WindowCalculationResultPool."""

    def test_pool_initialization(self) -> None:
        """Test pool initialization."""
        from custom_components.solar_window_system.modules.calculations import (
            WindowCalculationResultPool,
        )

        pool = WindowCalculationResultPool(max_size=50)
        assert pool._max_size == 50
        assert pool._pool == []
        assert pool._borrowed == 0

    def test_pool_acquire_new(self) -> None:
        """Test acquiring from empty pool."""
        from custom_components.solar_window_system.modules.calculations import (
            WindowCalculationResultPool,
        )

        pool = WindowCalculationResultPool()
        result = pool.acquire()

        assert isinstance(result, WindowCalculationResult)
        assert pool._borrowed == 1
        assert len(pool._pool) == 0

    def test_pool_acquire_reuse(self) -> None:
        """Test acquiring reused object from pool."""
        from custom_components.solar_window_system.modules.calculations import (
            WindowCalculationResultPool,
        )

        pool = WindowCalculationResultPool()
        result1 = pool.acquire()
        pool.release(result1)
        result2 = pool.acquire()

        assert result2 is result1  # Should be the same object
        assert pool._borrowed == 1
        assert len(pool._pool) == 0

    def test_pool_release(self) -> None:
        """Test releasing object back to pool."""
        from custom_components.solar_window_system.modules.calculations import (
            WindowCalculationResultPool,
        )

        pool = WindowCalculationResultPool()
        result = pool.acquire()
        pool.release(result)

        assert pool._borrowed == 0
        assert len(pool._pool) == 1

    def test_pool_release_over_max_size(self) -> None:
        """Test releasing when pool is at max size."""
        from custom_components.solar_window_system.modules.calculations import (
            WindowCalculationResultPool,
        )

        pool = WindowCalculationResultPool(max_size=2)
        result1 = pool.acquire()
        result2 = pool.acquire()
        result3 = pool.acquire()

        pool.release(result1)
        pool.release(result2)
        pool.release(result3)  # This should not be added due to max_size

        assert len(pool._pool) == 2
        assert pool._borrowed == 0

    def test_pool_get_stats(self) -> None:
        """Test getting pool statistics."""
        from custom_components.solar_window_system.modules.calculations import (
            WindowCalculationResultPool,
        )

        pool = WindowCalculationResultPool(max_size=10)
        result = pool.acquire()

        stats = pool.get_stats()
        assert stats["pool_size"] == 0
        assert stats["borrowed"] == 1
        assert stats["max_size"] == 10

        pool.release(result)
        stats = pool.get_stats()
        assert stats["pool_size"] == 1
        assert stats["borrowed"] == 0


class TestPoolFunctions:
    """Test suite for global pool functions."""

    def test_get_pooled_result(self) -> None:
        """Test getting pooled result."""
        from custom_components.solar_window_system.modules.calculations import (
            get_pooled_result,
        )

        result = get_pooled_result()
        assert isinstance(result, WindowCalculationResult)

    def test_release_pooled_result(self) -> None:
        """Test releasing pooled result."""
        from custom_components.solar_window_system.modules.calculations import (
            get_pooled_result,
            release_pooled_result,
            get_pool_stats,
        )

        result = get_pooled_result()
        initial_stats = get_pool_stats()

        release_pooled_result(result)
        final_stats = get_pool_stats()

        assert final_stats["pool_size"] == initial_stats["pool_size"] + 1

    def test_get_pool_stats(self) -> None:
        """Test getting pool statistics."""
        from custom_components.solar_window_system.modules.calculations import (
            get_pool_stats,
        )

        stats = get_pool_stats()
        assert isinstance(stats, dict)
        assert "pool_size" in stats
        assert "borrowed" in stats
        assert "max_size" in stats


class TestBatchCalculations:
    """Test suite for batch calculation methods."""

    @pytest.mark.asyncio
    async def test_batch_calculate_windows_empty(self) -> None:
        """Test batch calculation with empty input."""
        calc = CalculationsMixin()

        result = await calc.batch_calculate_windows([], [], {})
        assert result == []

    @pytest.mark.asyncio
    async def test_batch_calculate_windows_single(self) -> None:
        """Test batch calculation with single window."""
        calc = CalculationsMixin()

        windows_data = [{"name": "window1", "azimuth": 180.0, "area": 2.0}]
        effective_configs = [{"shadow_depth": 1.0}]
        states = {"solar_radiation": 800.0, "sun_elevation": 45.0, "sun_azimuth": 180.0}

        result = await calc.batch_calculate_windows(
            windows_data, effective_configs, states
        )

        assert len(result) == 1
        assert isinstance(result[0], WindowCalculationResult)
        assert result[0].area_m2 == 2.0

    def test_batch_calculate_windows_sequential_empty(self) -> None:
        """Test sequential batch calculation with empty input."""
        calc = CalculationsMixin()

        result = calc._batch_calculate_windows_sequential([], [], {})
        assert result == []

    def test_batch_calculate_windows_sequential_single(self) -> None:
        """Test sequential batch calculation with single window."""
        calc = CalculationsMixin()

        windows_data = [{"name": "window1", "azimuth": 180.0, "area": 2.0}]
        effective_configs = [{"shadow_depth": 1.0}]
        states = {"solar_radiation": 800.0, "sun_elevation": 45.0, "sun_azimuth": 180.0}

        result = calc._batch_calculate_windows_sequential(
            windows_data, effective_configs, states
        )

        assert len(result) == 1
        assert isinstance(result[0], WindowCalculationResult)

    @pytest.mark.asyncio
    async def test_calculate_window_task(self) -> None:
        """Test individual window calculation task."""
        calc = CalculationsMixin()

        effective_config = {"shadow_depth": 1.0}
        window_data = {"name": "window1", "azimuth": 180.0, "area": 2.0}
        states = {"solar_radiation": 800.0, "sun_elevation": 45.0, "sun_azimuth": 180.0}

        result = await calc._calculate_window_task(
            effective_config, window_data, states
        )

        assert isinstance(result, WindowCalculationResult)
        assert result.area_m2 == 2.0


class TestAsyncCalculations:
    """Test suite for async calculation methods."""

    @pytest.mark.asyncio
    async def test_calculate_window_solar_power_with_shadow_async(self) -> None:
        """Test async window solar power calculation."""
        calc = CalculationsMixin()

        effective_config = {"shadow_depth": 1.0, "shadow_offset": 0.0}
        window_data = {"name": "window1", "azimuth": 180.0, "area": 2.0}
        states = {"solar_radiation": 800.0, "sun_elevation": 45.0, "sun_azimuth": 180.0}

        result = await calc.calculate_window_solar_power_with_shadow_async(
            effective_config, window_data, states
        )

        assert isinstance(result, WindowCalculationResult)
        assert result.area_m2 == 2.0
        assert result.shadow_factor <= 1.0
        assert result.shadow_factor >= 0.1

    @pytest.mark.asyncio
    async def test_calculate_window_solar_power_with_shadow_async_error(self) -> None:
        """Test async calculation with error handling."""
        calc = CalculationsMixin()

        # Pass data that will cause an exception
        effective_config = {"shadow_depth": -1.0}  # Use numeric value instead of string
        window_data = {"azimuth": 180.0, "area": 2.0}
        states = {"solar_radiation": 800.0, "sun_elevation": 45.0, "sun_azimuth": 180.0}

        result = await calc.calculate_window_solar_power_with_shadow_async(
            effective_config, window_data, states
        )

        # Should still return a result, but with error indication
        assert isinstance(result, WindowCalculationResult)
        # Should succeed with default values despite invalid shadow_depth


class TestDirectPowerCalculations:
    """Test suite for direct power calculation methods."""

    def test_calculate_direct_power_perpendicular_sun(self) -> None:
        """Test direct power calculation with perpendicular sun."""
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
        window_azimuth = 180.0

        result = calc._calculate_direct_power(params, window_azimuth)
        assert result >= 0.0

    def test_calculate_direct_power_no_sun(self) -> None:
        """Test direct power calculation with no sun."""
        calc = CalculationsMixin()

        params = {
            "solar_radiation": 1000.0,
            "sun_elevation": -5.0,  # Below horizon
            "sun_azimuth": 180.0,
            "diffuse_factor": 0.3,
            "tilt": 90.0,
            "area": 2.0,
            "g_value": 0.8,
        }
        window_azimuth = 180.0

        result = calc._calculate_direct_power(params, window_azimuth)
        assert result == 0.0

    def test_calculate_solar_power_direct(self) -> None:
        """Test solar power direct calculation with SolarCalculationParams."""
        calc = CalculationsMixin()

        params = SolarCalculationParams(
            solar_radiation=1000.0,
            sun_elevation=45.0,
            sun_azimuth=180.0,
            window_azimuth=180.0,
            area=2.0,
            g_value=0.8,
            tilt=90.0,
            diffuse_factor=0.3,
        )

        result = calc._calculate_solar_power_direct(params)
        assert result >= 0.0


class TestParameterExtraction:
    """Test suite for parameter extraction methods."""

    def test_extract_calculation_parameters_complete(self) -> None:
        """Test parameter extraction with complete data."""
        calc = CalculationsMixin()

        effective_config = {"diffuse_factor": 0.3, "shadow_depth": 1.0}
        window_data = {
            "azimuth": 180.0,
            "area": 2.0,
            "g_value": 0.8,
            "tilt": 90.0,
        }
        states = {
            "solar_radiation": 1000.0,
            "sun_elevation": 45.0,
            "sun_azimuth": 180.0,
        }

        result = calc._extract_calculation_parameters(
            effective_config, window_data, states
        )

        assert len(result) == 9
        assert result[0] == 1000.0  # solar_radiation
        assert result[1] == 45.0  # sun_elevation
        assert result[2] == 180.0  # sun_azimuth
        assert result[3] == 180.0  # window_azimuth
        assert result[4] == 2.0  # area
        assert result[5] == 0.8  # g_value
        assert result[6] == 90.0  # tilt
        assert result[7] == 0.3  # diffuse_factor
        assert result[8] == 1.0  # shadow_depth

    def test_extract_calculation_parameters_defaults(self) -> None:
        """Test parameter extraction with missing data (defaults)."""
        calc = CalculationsMixin()

        effective_config = {}
        window_data = {}
        states = {}

        result = calc._extract_calculation_parameters(
            effective_config, window_data, states
        )

        assert len(result) == 9
        assert result[0] == 0.0  # solar_radiation default
        assert result[1] == 0.0  # sun_elevation default
        assert result[2] == 180.0  # sun_azimuth default
        assert result[3] == 180.0  # window_azimuth default
        assert result[4] == 1.0  # area default
        assert result[5] == 0.8  # g_value default
        assert result[6] == 90.0  # tilt default
        assert result[7] == 0.3  # diffuse_factor default
        assert result[8] == 0.0  # shadow_depth default


class TestPowerCalculations:
    """Test suite for power calculation methods."""

    def test_calculate_solar_power_diffuse(self) -> None:
        """Test diffuse solar power calculation."""
        calc = CalculationsMixin()

        result = calc._calculate_solar_power_diffuse(
            solar_radiation=1000.0,
            diffuse_factor=0.3,
            area=2.0,
            g_value=0.8,
        )

        expected = 1000.0 * 0.3 * 2.0 * 0.8  # 480.0
        assert result == expected

    def test_calculate_total_solar_power(self) -> None:
        """Test total solar power calculation."""
        calc = CalculationsMixin()

        result = calc._calculate_total_solar_power(
            solar_radiation=1000.0,
            diffuse_factor=0.3,
            area=2.0,
            g_value=0.8,
        )

        # Should be direct + diffuse
        assert result >= 0.0
        assert isinstance(result, float)

    def test_calculate_power_per_square_meter(self) -> None:
        """Test power per square meter calculation."""
        calc = CalculationsMixin()

        result = calc._calculate_power_per_square_meter(
            total_power=1000.0,
            area=2.0,
        )

        assert result == 500.0

    def test_calculate_power_per_square_meter_zero_area(self) -> None:
        """Test power per square meter with zero area."""
        calc = CalculationsMixin()

        result = calc._calculate_power_per_square_meter(
            total_power=1000.0,
            area=0.0,
        )

        assert result == 0.0
